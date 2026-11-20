from __future__ import annotations

from django import forms

from accounts.models import Commission
from django.utils import timezone

from .models import Event, Idea


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
        self.fields['commission'].queryset = Commission.objects.filter(is_hidden=False).order_by('sort_order', 'name')
        self.fields['commission'].required = False
        self.fields['commission'].empty_label = 'Не знаю / інше (без комісії)'


class IdeaStatusForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].choices = [choice for choice in Idea.Status.choices if choice[0] != Idea.Status.SUBMITTED]

    class Meta:
        model = Idea
        fields = ['status', 'status_reason', 'completion_report']
        labels = {
            'status': 'Статус',
            'status_reason': 'Причина',
            'completion_report': 'Публікаційний звіт',
        }


class EventCreateForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'starts_at', 'organiser', 'participating_classes', 'outcome']
        labels = {
            'title': 'Назва події',
            'description': 'Опис події',
            'starts_at': 'Дата та час проведення',
            'organiser': 'Організатор',
            'participating_classes': 'Залучені класи',
            'outcome': 'Результат (можна заповнити після проведення)',
        }
        widgets = {
            'starts_at': forms.DateTimeInput(
                format='%Y-%m-%dT%H:%M',
                attrs={'type': 'datetime-local'},
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['starts_at'].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['organiser'].required = False
        self.fields['participating_classes'].required = False
        self.fields['outcome'].required = False

    def clean_starts_at(self):
        value = self.cleaned_data['starts_at']
        if value <= timezone.now():
            raise forms.ValidationError('Дата та час події мають бути в майбутньому.')
        return value
