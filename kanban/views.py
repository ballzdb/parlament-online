from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import Commission, User
from app.permissions import requires_roles
from .forms import KanbanCardForm
from .models import KanbanCard


def board_list(request, slug=None):
    commission = None
    if slug:
        commission = get_object_or_404(Commission, slug=slug)
        cards = KanbanCard.objects.filter(commission=commission).select_related('commission', 'assignee').order_by('position', 'created_at')
    else:
        cards = KanbanCard.objects.select_related('commission', 'assignee').order_by('commission__sort_order', 'position', 'created_at')
    commissions = Commission.objects.order_by('sort_order', 'name')
    status_columns = [
        ('todo', 'До виконання'),
        ('in_progress', 'У роботі'),
        ('done', 'Готово'),
    ]
    return render(request, 'kanban/board.html', {'cards': cards, 'commission': commission, 'commissions': commissions, 'status_columns': status_columns})


@login_required
@requires_roles(User.Role.MEMBER, User.Role.COMMISSION_HEAD, User.Role.SECRETARY)
def card_edit(request, pk):
    card = get_object_or_404(KanbanCard, pk=pk)
    if not request.user.is_member:
        messages.error(request, 'Тільки члени парламенту можуть редагувати картки.')
        return redirect('kanban:board')
    if request.method == 'POST':
        form = KanbanCardForm(request.POST, instance=card)
        if form.is_valid():
            form.save()
            messages.success(request, 'Картку оновлено.')
            return redirect('kanban:commission_board', slug=card.commission.slug)
    else:
        form = KanbanCardForm(instance=card)
    return render(request, 'kanban/card_edit.html', {'form': form, 'card': card})
