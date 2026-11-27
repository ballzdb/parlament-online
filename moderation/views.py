from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import AuditLog, User
from app.permissions import requires_roles
from ideas.models import Idea
from .models import ModerationEntry
from .forms import IdeaRejectionForm, REJECTION_CATEGORIES, TemporaryRestrictionForm


MODERATOR_ROLES = (User.Role.SECRETARY, User.Role.COMMISSION_HEAD, User.Role.MODERATOR)
REJECTION_CATEGORY_LABELS = dict(REJECTION_CATEGORIES)


def record_moderation_event(idea, actor, action, reason='', category='', assigned_moderator=None):
    """Keep a human-readable, append-only record of each moderation decision."""
    verdict = {
        'action': action,
        'actor_id': actor.pk,
        'actor_email': actor.email,
        'actor_name': actor.display_name or actor.email,
        'reason': reason,
    }
    if category:
        verdict['category'] = category
        verdict['category_label'] = REJECTION_CATEGORY_LABELS.get(category, '')
    if assigned_moderator is not None:
        verdict['assigned_moderator_id'] = assigned_moderator.pk
        verdict['assigned_moderator_email'] = assigned_moderator.email
        verdict['assigned_moderator_name'] = assigned_moderator.display_name or assigned_moderator.email
    ModerationEntry.objects.create(
        target_type='idea',
        target_id=idea.pk,
        verdict=verdict,
    )


def can_moderate_idea(user, idea):
    """Global moderators and secretaries can manage all ideas; commission heads only assigned ones."""
    if user.has_role(User.Role.SECRETARY, User.Role.MODERATOR):
        return True
    return user.has_role(User.Role.COMMISSION_HEAD) and idea.assigned_moderator_id == user.pk


@login_required
@requires_roles(*MODERATOR_ROLES)
def moderation_queue(request):
    pending_ideas = Idea.objects.filter(
        moderation_status=Idea.ModerationStatus.PENDING
    ).select_related('author', 'commission', 'assigned_moderator').order_by('created_at')
    published_ideas = Idea.objects.filter(
        moderation_status=Idea.ModerationStatus.APPROVED
    ).select_related('author', 'commission', 'assigned_moderator').order_by('-moderated_at', '-created_at')[:30]
    moderators = [
        user for user in User.objects.filter(is_active=True).order_by('display_name', 'email')
        if user.has_role(*MODERATOR_ROLES)
    ]
    return render(request, 'moderation/queue.html', {
        'ideas': pending_ideas,
        'published_ideas': published_ideas,
        'moderators': moderators,
        'rejection_categories': REJECTION_CATEGORIES,
    })


@login_required
@require_POST
@requires_roles(*MODERATOR_ROLES)
def moderate_idea(request, pk):
    idea = get_object_or_404(Idea, pk=pk, moderation_status=Idea.ModerationStatus.PENDING)
    action = request.POST.get('action', '').strip()
    is_secretary = request.user.has_role(User.Role.SECRETARY)

    if action == 'assign':
        if not is_secretary:
            raise PermissionDenied
        moderator_id = request.POST.get('moderator')
        moderator = get_object_or_404(User, pk=moderator_id, is_active=True)
        if not moderator.has_role(*MODERATOR_ROLES):
            raise PermissionDenied
        idea.assigned_moderator = moderator
        idea.save(update_fields=['assigned_moderator', 'updated_at'])
        record_moderation_event(idea, request.user, 'assigned', assigned_moderator=moderator)
        AuditLog.objects.create(
            action='idea_moderator_assigned', user=request.user, email=request.user.email,
            details=f'Idea #{idea.pk} assigned to {moderator.email}',
        )
        messages.success(request, 'Відповідального модератора призначено.')
    elif action in {'approve', 'reject'}:
        if not can_moderate_idea(request.user, idea):
            raise PermissionDenied

        reason = ''
        category = ''
        if action == 'reject':
            rejection_form = IdeaRejectionForm(request.POST)
            if not rejection_form.is_valid():
                messages.error(request, 'Оберіть категорію відхилення. Додаткове пояснення можна не заповнювати.')
                return redirect('moderation:queue')
            category = rejection_form.cleaned_data['category']
            category_label = REJECTION_CATEGORY_LABELS[category]
            comment = rejection_form.cleaned_data['comment'].strip()
            reason = f'{category_label}.'
            if comment:
                reason = f'{reason} {comment}'

        idea.moderation_status = (
            Idea.ModerationStatus.APPROVED if action == 'approve'
            else Idea.ModerationStatus.REJECTED
        )
        idea.moderation_reason = reason
        idea.moderated_by = request.user
        idea.moderated_at = timezone.now()
        idea.status = Idea.Status.SUBMITTED if action == 'approve' else Idea.Status.REJECTED
        idea.save(update_fields=[
            'moderation_status', 'moderation_reason', 'moderated_by',
            'moderated_at', 'status', 'updated_at',
        ])
        record_moderation_event(idea, request.user, action, reason=reason, category=category)
        AuditLog.objects.create(
            action=f'idea_moderation_{action}', user=request.user, email=request.user.email,
            details=f'Idea #{idea.pk}: {action}; category={category}; reason={reason}',
        )
        messages.success(request, 'Ідею опубліковано.' if action == 'approve' else 'Ідею відхилено.')
    else:
        messages.error(request, 'Невідома дія модерації.')

    return redirect('moderation:queue')


@login_required
@require_POST
@requires_roles(*MODERATOR_ROLES)
def delete_idea(request, pk):
    idea = get_object_or_404(Idea, pk=pk)
    if not can_moderate_idea(request.user, idea):
        raise PermissionDenied

    title = idea.title
    idea_id = idea.pk
    with transaction.atomic():
        record_moderation_event(idea, request.user, 'deleted', reason='Видалено модератором.')
        AuditLog.objects.create(
            action='idea_deleted_by_moderator',
            user=request.user,
            email=request.user.email,
            details=f'Idea #{idea_id} "{title}" deleted by {request.user.email}',
        )
        idea.delete()

    messages.success(request, 'Ідею видалено.')
    return redirect('moderation:queue')


@login_required
@requires_roles(*MODERATOR_ROLES)
def sanctions(request):
    if request.method == 'POST':
        form = TemporaryRestrictionForm(request.POST)
        if form.is_valid():
            student = form.cleaned_data['user']
            student.restricted_until = form.cleaned_data['restricted_until']
            student.restriction_reason = form.cleaned_data['reason']
            student.restricted_by = request.user
            student.save(update_fields=['restricted_until', 'restriction_reason', 'restricted_by'])
            AuditLog.objects.create(
                action='student_temporarily_restricted',
                user=request.user,
                email=request.user.email,
                details=f'{student.email} restricted until {student.restricted_until.isoformat()}: {student.restriction_reason}',
            )
            messages.success(request, 'Тимчасове обмеження застосовано.')
            return redirect('moderation:sanctions')
    else:
        form = TemporaryRestrictionForm()

    active_restrictions = User.objects.filter(
        restricted_until__gt=timezone.now()
    ).select_related('restricted_by').order_by('restricted_until')
    return render(request, 'moderation/sanctions.html', {
        'form': form,
        'active_restrictions': active_restrictions,
    })


@login_required
@require_POST
@requires_roles(*MODERATOR_ROLES)
def clear_sanction(request, pk):
    student = get_object_or_404(User, pk=pk)
    student.restricted_until = None
    student.restriction_reason = ''
    student.restricted_by = None
    student.save(update_fields=['restricted_until', 'restriction_reason', 'restricted_by'])
    AuditLog.objects.create(
        action='student_temporary_restriction_cleared',
        user=request.user,
        email=request.user.email,
        details=f'Temporary restriction cleared for {student.email}',
    )
    messages.success(request, 'Обмеження достроково знято.')
    return redirect('moderation:sanctions')


def moderation_rules(request):
    return render(request, 'moderation/rules.html')
