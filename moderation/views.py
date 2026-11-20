from __future__ import annotations
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from accounts.models import AuditLog, User
from app.permissions import requires_roles
from ideas.models import Idea
from .models import ModerationEntry

@login_required
@requires_roles(User.Role.SECRETARY)
def moderation_queue(request):
    ideas = Idea.objects.filter(status=Idea.Status.SUBMITTED).select_related('author','commission').order_by('created_at')
    return render(request, 'moderation/queue.html', {'ideas': ideas})

@login_required
@requires_roles(User.Role.SECRETARY)
@require_POST
def review_idea(request, pk):
    idea = get_object_or_404(Idea, pk=pk, status=Idea.Status.SUBMITTED)
    action = request.POST.get('action')
    reason = request.POST.get('reason','').strip()[:2000]
    if action == 'approve':
        idea.status, idea.status_reason, verdict = Idea.Status.UNDER_REVIEW, '', 'approved'
        notice = 'Ідею схвалено й опубліковано на загальній дошці.'
    elif action == 'reject':
        if not reason:
            messages.error(request, 'Для відхилення потрібно вказати причину.')
            return redirect('moderation:queue')
        idea.status, idea.status_reason, verdict = Idea.Status.REJECTED, reason, 'rejected'
        notice = 'Ідею відхилено. Автор побачить пояснення.'
    else:
        raise PermissionDenied
    with transaction.atomic():
        idea.save(update_fields=['status','status_reason','updated_at'])
        ModerationEntry.objects.create(target_type='idea', target_id=idea.pk, verdict={'decision':verdict,'moderator':request.user.email,'reason':reason})
        AuditLog.objects.create(action='idea_moderation_'+verdict,email=request.user.email,user=request.user,details=f'Idea #{idea.pk}: {verdict}; {reason}')
    messages.success(request, notice)
    return redirect('moderation:queue')
