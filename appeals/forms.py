from __future__ import annotations

from django import forms

from .models import Appeal


class AppealForm(forms.ModelForm):
    class Meta:
        model = Appeal
        fields = ['kind', 'subject', 'body', 'visibility']
        labels = {
            'kind': 'Тип звернення',
            'subject': 'Тема',
            'body': 'Повідомлення',
            'visibility': 'Видимість',
        }
        widgets = {
            'body': forms.Textarea(attrs={'rows': 6}),
        }
