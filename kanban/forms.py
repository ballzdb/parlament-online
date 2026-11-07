from __future__ import annotations

from django import forms

from accounts.models import User
from .models import KanbanCard


class KanbanCardForm(forms.ModelForm):
    class Meta:
        model = KanbanCard
        fields = ['title', 'description', 'assignee', 'due_date', 'status']
        labels = {
            'title': 'Назва',
            'description': 'Опис',
            'assignee': 'Відповідальний',
            'due_date': 'Термін виконання',
            'status': 'Статус',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assignee'].queryset = User.objects.filter(role__in=[User.Role.MEMBER, User.Role.COMMISSION_HEAD, User.Role.SECRETARY]).order_by('email')
