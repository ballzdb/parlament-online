from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import AuditLog, User
from app.permissions import requires_roles
from ideas.models import Idea
from .models import ModerationEntry


MODERATOR_ROLES = (User.Role.SECRETARY, User.Role.COMMISSION_HEAD)


@login_required
@requires_roles(*MODERATOR_ROLES)
def moderation_queue(request):
    pending_ideas = Idea.objects.filter(
        moderation_status=Idea.ModerationStatus.PENDING
    ).select_related('author', 'commission', 'assigned_moderator').order_by('created_at')
    moderators = User.objects.filter(
        is_active=True, role__in=MODERATOR_ROLES
    ).order_by('display_name', 'email')
    return render(request, 'moderation/queue.html', {
        'ideas': pending_ideas,
        'moderators': moderators,
    })


@login_required
@require_POST
@requires_roles(*MODERATOR_ROLES)
def moderate_idea(request, pk):
    idea = get_object_or_404(Idea, pk=pk, moderation_status=Idea.ModerationStatus.PENDING)
    action = request.POST.get('action', '').strip()
    is_secretary = request.user.role == User.Role.SECRETARY

    if action == 'assign':
        if not is_secretary:
            raise PermissionDenied
        moderator_id = request.POST.get('moderator')
        moderator = get_object_or_404(User, pk=moderator_id, is_active=True, role__in=MODERATOR_ROLES)
        idea.assigned_moderator = moderator
        idea.save(update_fields=['assigned_moderator', 'updated_at'])
        AuditLog.objects.create(
            action='idea_moderator_assigned', user=request.user, email=request.user.email,
            details=f'Idea #{idea.pk} assigned to {moderator.email}',
        )
        messages.success(request, 'Відповідального модератора призначено.')
    elif action in {'approve', 'reject'}:
        if not is_secretary and idea.assigned_moderator_id != request.user.pk:
            raise PermissionDenied
        reason = request.POST.get('reason', '').strip()
        if action == 'reject' and not reason:
            messages.error(request, 'Для відхилення обов’язково вкажіть причину.')
            return redirect('moderation:queue')
        idea.moderation_status = (
            Idea.ModerationStatus.APPROVED if action == 'approve'
            else Idea.ModerationStatus.REJECTED
        )
        idea.moderation_reason = reason
        idea.moderated_by = request.user
        idea.moderated_at = timezone.now()
        if action == 'approve':
            idea.status = Idea.Status.SUBMITTED
        else:
            idea.status = Idea.Status.REJECTED
        idea.save(update_fields=[
            'moderation_status', 'moderation_reason', 'moderated_by',
            'moderated_at', 'status', 'updated_at',
        ])
        AuditLog.objects.create(
            action=f'idea_moderation_{action}', user=request.user, email=request.user.email,
            details=f'Idea #{idea.pk}: {action}; reason={reason}',
        )
        messages.success(request, 'Ідею опубліковано.' if action == 'approve' else 'Ідею відхилено.')
    else:
        messages.error(request, 'Невідома дія модерації.')

    return redirect('moderation:queue')
