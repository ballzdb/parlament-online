from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.db.models import F
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import AuditLog, Commission, PRIMARY_ADMIN_EMAIL, User
from appeals.models import Appeal
from .forms import EventCreateForm, IdeaForm, IdeaStatusForm
from .models import Event, Idea, IdeaVote


def home(request):
    ideas = Idea.objects.select_related('commission', 'author').order_by('-created_at')[:6]
    appeals = Appeal.objects.order_by('-created_at')[:5]
    events = Event.objects.filter(starts_at__gte=timezone.now()).select_related('created_by', 'source_idea')[:6]
    context = {
        'ideas': ideas,
        'appeals': appeals,
        'events': events,
        'stats': {
            'idea_count': Idea.objects.count(),
            'appeal_count': Appeal.objects.count(),
        },
    }
    return render(request, 'home.html', context)


def idea_list(request):
    ideas = Idea.objects.select_related('commission', 'author').order_by('-vote_count', '-created_at')
    return render(request, 'ideas/list.html', {'ideas': ideas})


@login_required
def idea_create(request):
    if request.method == 'POST':
        form = IdeaForm(request.POST)
        if form.is_valid():
            idea = form.save(commit=False)
            idea.author = request.user
            idea.save()
            messages.success(request, 'Ідея успішно подана й відправлена на розгляд.')
            return redirect('ideas:list')
    else:
        form = IdeaForm()
    return render(request, 'ideas/create.html', {'form': form})


@login_required
def idea_detail(request, pk):
    idea = get_object_or_404(Idea, pk=pk)
    has_voted = IdeaVote.objects.filter(idea=idea, user=request.user).exists()
    status_form = None
    if request.user.has_role(request.user.Role.MEMBER, request.user.Role.COMMISSION_HEAD, request.user.Role.SECRETARY):
        if request.method == 'POST':
            status_form = IdeaStatusForm(request.POST, instance=idea)
            if status_form.is_valid():
                status_form.save()
                messages.success(request, 'Статус ідеї оновлено.')
                return redirect('ideas:detail', pk=idea.pk)
        else:
            status_form = IdeaStatusForm(instance=idea)

    if request.method == 'POST' and 'vote' in request.POST and not has_voted:
        try:
            with transaction.atomic():
                IdeaVote.objects.create(idea=idea, user=request.user)
                Idea.objects.filter(pk=idea.pk).update(vote_count=F('vote_count') + 1)
            messages.success(request, 'Ваш голос додано.')
        except IntegrityError:
            messages.error(request, 'Ви вже голосували за цю ідею.')
        return redirect('ideas:detail', pk=idea.pk)

    return render(request, 'ideas/detail.html', {'idea': idea, 'has_voted': has_voted, 'status_form': status_form})



@login_required
def event_create(request, pk):
    if not request.user.has_role(
        User.Role.MEMBER, User.Role.COMMISSION_HEAD, User.Role.SECRETARY
    ):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    idea = get_object_or_404(Idea, pk=pk)
    if request.method == 'POST':
        form = EventCreateForm(request.POST, initial={
            'title': idea.title,
            'description': idea.body,
        })
        if form.is_valid():
            event = form.save(commit=False)
            event.source_idea = idea
            event.created_by = request.user
            event.save()
            messages.success(request, 'Подію створено. Вона з’явиться на головній сторінці.')
            return redirect('ideas:detail', pk=idea.pk)
    else:
        form = EventCreateForm(initial={
            'title': idea.title,
            'description': idea.body,
        })
    return render(request, 'ideas/event_create.html', {'form': form, 'idea': idea})



@login_required
def idea_delete(request, pk):
    if request.method != 'POST':
        from django.http import HttpResponseNotAllowed
        return HttpResponseNotAllowed(['POST'])

    is_admin = request.user.email.casefold() == PRIMARY_ADMIN_EMAIL
    is_parliamentarian = request.user.role == User.Role.MEMBER
    if not (is_admin or is_parliamentarian):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    idea = get_object_or_404(Idea, pk=pk)
    title = idea.title
    idea_id = idea.pk
    AuditLog.objects.create(
        action='idea_deleted',
        email=request.user.email,
        user=request.user,
        details=f'Idea #{idea_id} "{title}" deleted by {request.user.email}',
    )
    idea.delete()
    messages.success(request, 'Ідею видалено.')
    return redirect('ideas:list')
