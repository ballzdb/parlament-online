from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import Commission, User
from app.permissions import requires_roles
from .forms import KanbanCardForm, TaskCommentForm, TaskCreateForm
from .models import KanbanCard


PARLIAMENT_ROLES = (User.Role.MEMBER, User.Role.COMMISSION_HEAD, User.Role.SECRETARY)


def board_list(request, slug=None):
    commission = None
    if slug:
        commission = get_object_or_404(Commission, slug=slug, is_hidden=False)
        cards = KanbanCard.objects.filter(commission=commission)
    else:
        cards = KanbanCard.objects.filter(commission__is_hidden=False)

    cards = list(cards.select_related('commission', 'assignee', 'created_by').prefetch_related('comments').order_by('commission__sort_order', 'position', 'created_at'))
    status_columns = [
        ('todo', 'До виконання'),
        ('in_progress', 'У роботі'),
        ('done', 'Виконано'),
    ]
    grouped_cards = {
        key: [card for card in cards if card.status == key]
        for key, _label in status_columns
    }
    commissions = Commission.objects.filter(is_hidden=False).order_by('sort_order', 'name')
    return render(request, 'kanban/board.html', {
        'grouped_cards': grouped_cards,
        'commission': commission,
        'commissions': commissions,
        'status_columns': status_columns,
        'can_manage_tasks': request.user.is_authenticated and request.user.has_role(*PARLIAMENT_ROLES),
    })


@login_required
@requires_roles(*PARLIAMENT_ROLES)
def card_create(request):
    initial = {}
    slug = request.GET.get('commission')
    if slug:
        initial['commission'] = get_object_or_404(Commission, slug=slug, is_hidden=False)
    if request.method == 'POST':
        form = TaskCreateForm(request.POST)
        if form.is_valid():
            card = form.save(commit=False)
            card.created_by = request.user
            card.save()
            messages.success(request, 'Завдання додано до дошки.')
            return redirect('kanban:card_detail', pk=card.pk)
    else:
        form = TaskCreateForm(initial=initial)
    return render(request, 'kanban/card_create.html', {'form': form})


@login_required
def card_detail(request, pk):
    card = get_object_or_404(
        KanbanCard.objects.select_related('commission', 'assignee', 'created_by').prefetch_related('comments__author'),
        pk=pk,
    )
    can_manage_tasks = request.user.has_role(*PARLIAMENT_ROLES)
    if request.method == 'POST':
        if not can_manage_tasks:
            raise PermissionDenied
        form = TaskCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.card = card
            comment.author = request.user
            comment.save()
            messages.success(request, 'Коментар додано.')
            return redirect('kanban:card_detail', pk=card.pk)
    else:
        form = TaskCommentForm()
    return render(request, 'kanban/card_detail.html', {
        'card': card,
        'comment_form': form,
        'can_manage_tasks': can_manage_tasks,
    })


@login_required
@requires_roles(*PARLIAMENT_ROLES)
def card_edit(request, pk):
    card = get_object_or_404(KanbanCard, pk=pk)
    if request.method == 'POST':
        form = KanbanCardForm(request.POST, instance=card)
        if form.is_valid():
            form.save()
            messages.success(request, 'Завдання оновлено.')
            return redirect('kanban:card_detail', pk=card.pk)
    else:
        form = KanbanCardForm(instance=card)
    return render(request, 'kanban/card_edit.html', {'form': form, 'card': card})
