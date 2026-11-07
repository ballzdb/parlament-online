from __future__ import annotations

from django import forms

from accounts.models import Commission
from .models import Idea


class IdeaForm(forms.ModelForm):
    class Meta:
        model = Idea
        fields = ['title', 'body', 'commission']
        labels = {
            'title': 'Назва ідеї',
            'body': 'Опис',
            'commission': 'Комісія',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['commission'].queryset = Commission.objects.all().order_by('sort_order', 'name')
        self.fields['commission'].required = False


class IdeaStatusForm(forms.ModelForm):
    class Meta:
        model = Idea
        fields = ['status', 'status_reason', 'completion_report']
        labels = {
            'status': 'Статус',
            'status_reason': 'Причина',
            'completion_report': 'Публікаційний звіт',
        }
