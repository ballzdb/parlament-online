from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import AuditLog, User
from ideas.models import Idea
from .forms import AppealForm, AppealStaffForm
from .models import Appeal


def appeal_list(request):
    if request.user.is_authenticated:
        queryset = Appeal.objects.filter(
            Q(author=request.user) | Q(visibility=Appeal.Visibility.PUBLIC)
        )
    else:
        queryset = Appeal.objects.filter(visibility=Appeal.Visibility.PUBLIC)
    if request.user.is_authenticated and not request.user.is_student:
        queryset = Appeal.objects.all()
    return render(request, 'appeals/list.html', {
        'appeals': queryset.distinct().select_related('author', 'related_idea'),
    })


@login_required
def appeal_create(request):
    idea_id = request.POST.get('related_idea_id') or request.GET.get('idea')
    idea = None
    initial = {}
    if idea_id:
        idea = get_object_or_404(
            Idea,
            pk=idea_id,
            author=request.user,
            moderation_status=Idea.ModerationStatus.REJECTED,
        )
        initial = {
            'kind': Appeal.Kind.MODERATION,
            'subject': f'Оскарження рішення щодо ідеї «{idea.title}»',
            'visibility': Appeal.Visibility.PRIVATE,
        }

    if request.method == 'POST':
        form = AppealForm(request.POST, initial=initial)
        if form.is_valid():
            appeal = form.save(commit=False)
            appeal.author = request.user
            if idea:
                appeal.related_idea = idea
                appeal.kind = Appeal.Kind.MODERATION
                appeal.visibility = Appeal.Visibility.PRIVATE
            appeal.save()
            messages.success(request, 'Звернення надіслано. Його бачите ви та уповноважені представники парламенту.')
            return redirect('appeals:list')
    else:
        form = AppealForm(initial=initial)

    return render(request, 'appeals/create.html', {'form': form, 'idea': idea})


@login_required
def appeal_manage(request, pk):
    if request.user.role != User.Role.SECRETARY:
        raise PermissionDenied

    appeal = get_object_or_404(
        Appeal.objects.select_related('author', 'related_idea'),
        pk=pk,
    )
    if request.method == 'POST':
        form = AppealStaffForm(request.POST, instance=appeal)
        if form.is_valid():
            form.save()
            AuditLog.objects.create(
                action='appeal_updated',
                user=request.user,
                email=request.user.email,
                details=f'Appeal #{appeal.pk} status changed to {appeal.status}',
            )
            messages.success(request, 'Відповідь і стан звернення оновлено.')
            return redirect('appeals:list')
    else:
        form = AppealStaffForm(instance=appeal)

    return render(request, 'appeals/manage.html', {'form': form, 'appeal': appeal})
