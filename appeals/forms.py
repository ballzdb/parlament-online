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

    def clean_kind(self):
        kind = self.cleaned_data['kind']
        if kind == Appeal.Kind.MODERATION and self.initial.get('kind') != Appeal.Kind.MODERATION:
            raise forms.ValidationError('Оскаржити можна лише конкретне рішення щодо власної відхиленої ідеї.')
        return kind


class AppealStaffForm(forms.ModelForm):
    class Meta:
        model = Appeal
        fields = ['status', 'public_answer']
        labels = {
            'status': 'Стан звернення',
            'public_answer': 'Відповідь автору',
        }
        widgets = {
            'public_answer': forms.Textarea(attrs={'rows': 5}),
        }
