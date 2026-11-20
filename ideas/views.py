from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.db.models import F, Q
from django.http import Http404, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import AuditLog, Commission, PRIMARY_ADMIN_EMAIL, User
from appeals.models import Appeal
from .forms import EventCreateForm, IdeaForm, IdeaStatusForm
from .models import Event, Idea, IdeaVote


PARLIAMENT_ROLES = (User.Role.MEMBER, User.Role.COMMISSION_HEAD, User.Role.SECRETARY)


def home(request):
    ideas = Idea.objects.filter(moderation_status=Idea.ModerationStatus.APPROVED).select_related('commission', 'author').order_by('-created_at')[:6]
    appeals = Appeal.objects.order_by('-created_at')[:5]
    events = Event.objects.filter(starts_at__gte=timezone.now()).select_related('created_by', 'source_idea')[:6]
    context = {
        'ideas': ideas,
        'appeals': appeals,
        'events': events,
        'stats': {
            'idea_count': Idea.objects.filter(moderation_status=Idea.ModerationStatus.APPROVED).count(),
            'appeal_count': Appeal.objects.count(),
        },
    }
    return render(request, 'home.html', context)


def idea_list(request):
    ideas = Idea.objects.select_related('commission', 'author').order_by('-vote_count', '-created_at')
    if not request.user.is_authenticated:
        ideas = ideas.filter(moderation_status=Idea.ModerationStatus.APPROVED)
    elif request.user.has_role(*PARLIAMENT_ROLES):
        pass
    else:
        ideas = ideas.filter(
            Q(moderation_status=Idea.ModerationStatus.APPROVED) | Q(author=request.user)
        )
    return render(request, 'ideas/list.html', {'ideas': ideas})


@login_required
def idea_create(request):
    if request.method == 'POST':
        form = IdeaForm(request.POST)
        if form.is_valid():
            idea = form.save(commit=False)
            idea.author = request.user
            idea.moderation_status = Idea.ModerationStatus.PENDING
            idea.status = Idea.Status.UNDER_REVIEW
            idea.save()
            messages.success(request, 'Ідею надіслано на модерацію. Вона з’явиться у загальному списку після перевірки.')
            return redirect('ideas:list')
    else:
        form = IdeaForm()
    return render(request, 'ideas/create.html', {'form': form})


@login_required
def idea_detail(request, pk):
    idea = get_object_or_404(Idea.objects.select_related('author', 'commission', 'assigned_moderator'), pk=pk)
    is_parliamentarian = request.user.has_role(*PARLIAMENT_ROLES)
    if idea.moderation_status != Idea.ModerationStatus.APPROVED and idea.author_id != request.user.pk and not is_parliamentarian:
        raise Http404

    has_voted = IdeaVote.objects.filter(idea=idea, user=request.user).exists()
    status_form = None
    if is_parliamentarian and idea.moderation_status == Idea.ModerationStatus.APPROVED:
        if request.method == 'POST' and 'status' in request.POST:
            status_form = IdeaStatusForm(request.POST, instance=idea)
            if status_form.is_valid():
                status_form.save()
                messages.success(request, 'Статус ідеї оновлено.')
                return redirect('ideas:detail', pk=idea.pk)
        else:
            status_form = IdeaStatusForm(instance=idea)

    if request.method == 'POST' and 'vote' in request.POST:
        if idea.moderation_status != Idea.ModerationStatus.APPROVED:
            messages.error(request, 'Голосування за ідею ще не відкрите.')
        elif has_voted:
            messages.error(request, 'Ви вже голосували за цю ідею.')
        else:
            try:
                with transaction.atomic():
                    IdeaVote.objects.create(idea=idea, user=request.user)
                    Idea.objects.filter(pk=idea.pk).update(vote_count=F('vote_count') + 1)
                messages.success(request, 'Ваш голос додано.')
            except IntegrityError:
                messages.error(request, 'Ви вже голосували за цю ідею.')
        return redirect('ideas:detail', pk=idea.pk)

    return render(request, 'ideas/detail.html', {
        'idea': idea,
        'has_voted': has_voted,
        'status_form': status_form,
        'is_parliamentarian': is_parliamentarian,
    })


@login_required
def event_create(request, pk):
    if not request.user.has_role(*PARLIAMENT_ROLES):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    idea = get_object_or_404(Idea, pk=pk)
    if idea.moderation_status != Idea.ModerationStatus.APPROVED:
        raise Http404
    initial = {
        'title': idea.title,
        'description': idea.body,
        'organiser': 'Учнівське самоврядування',
    }
    if request.method == 'POST':
        form = EventCreateForm(request.POST, initial=initial)
        if form.is_valid():
            event = form.save(commit=False)
            event.source_idea = idea
            event.created_by = request.user
            event.save()
            messages.success(request, 'Подію створено. Вона з’явиться в календарі та архіві.')
            return redirect('ideas:detail', pk=idea.pk)
    else:
        form = EventCreateForm(initial=initial)
    return render(request, 'ideas/event_create.html', {'form': form, 'idea': idea})


def event_list(request):
    now = timezone.now()
    upcoming = Event.objects.filter(starts_at__gte=now).select_related('created_by', 'source_idea')
    past = Event.objects.filter(starts_at__lt=now).select_related('created_by', 'source_idea').order_by('-starts_at')
    return render(request, 'ideas/events.html', {'upcoming_events': upcoming, 'past_events': past})


def event_detail(request, pk):
    event = get_object_or_404(Event.objects.select_related('created_by', 'source_idea'), pk=pk)
    return render(request, 'ideas/event_detail.html', {'event': event})


@login_required
def event_edit(request, pk):
    if not request.user.has_role(*PARLIAMENT_ROLES):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    event = get_object_or_404(Event, pk=pk)
    if request.method == 'POST':
        form = EventCreateForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, 'Інформацію про подію оновлено.')
            return redirect('ideas:event_detail', pk=event.pk)
    else:
        form = EventCreateForm(instance=event)
    return render(request, 'ideas/event_edit.html', {'form': form, 'event': event})


@login_required
def idea_delete(request, pk):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    is_admin = request.user.email.casefold() == PRIMARY_ADMIN_EMAIL
    is_parliamentarian = request.user.is_member
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
