from __future__ import annotations

from django import forms
from django.utils import timezone

from accounts.models import User


class TemporaryRestrictionForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True, role=User.Role.STUDENT).order_by('grade', 'class_letter', 'display_name'),
        label='Обліковий запис учня',
    )
    restricted_until = forms.DateTimeField(
        label='Обмежити до',
        input_formats=['%Y-%m-%dT%H:%M'],
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
    )
    reason = forms.CharField(
        label='Причина обмеження',
        min_length=10,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Опишіть конкретне порушення правила'}),
    )

    def clean_restricted_until(self):
        value = self.cleaned_data['restricted_until']
        if value <= timezone.now():
            raise forms.ValidationError('Час завершення обмеження має бути в майбутньому.')
        return value
