from __future__ import annotations

from django import forms
from django.core.validators import URLValidator

from accounts.models import Commission, User
from .models import KanbanCard, TaskComment


class KanbanCardForm(forms.ModelForm):
    class Meta:
        model = KanbanCard
        fields = ['title', 'description', 'reference_url', 'image_url', 'assignee', 'due_date', 'status']
        labels = {
            'title': 'Назва завдання',
            'description': 'Що потрібно зробити',
            'reference_url': 'Посилання на матеріали або документ',
            'image_url': 'Посилання на зображення (HTTPS)',
            'assignee': 'Відповідальний',
            'due_date': 'Термін виконання',
            'status': 'Статус',
        }
        widgets = {'due_date': forms.DateInput(attrs={'type': 'date'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        parliamentarians = [
            user.pk for user in User.objects.filter(is_active=True)
            if user.has_role(User.Role.MEMBER, User.Role.COMMISSION_HEAD, User.Role.SECRETARY)
        ]
        self.fields['assignee'].queryset = User.objects.filter(
            pk__in=parliamentarians
        ).order_by('display_name', 'email')
        self.fields['assignee'].required = False
        self.fields['reference_url'] = forms.URLField(required=False, label='Посилання на матеріали або документ', validators=[URLValidator(schemes=['https'])], widget=forms.URLInput(attrs={'placeholder': 'https://...'}))
        self.fields['image_url'] = forms.URLField(required=False, label='Посилання на зображення (HTTPS)', validators=[URLValidator(schemes=['https'])], widget=forms.URLInput(attrs={'placeholder': 'https://...'}))


class TaskCreateForm(KanbanCardForm):
    class Meta(KanbanCardForm.Meta):
        fields = ['commission', 'title', 'description', 'reference_url', 'image_url', 'assignee', 'due_date']
        labels = {**KanbanCardForm.Meta.labels, 'commission': 'Комісія'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['commission'] = forms.ModelChoiceField(
            queryset=Commission.objects.filter(is_hidden=False).order_by('sort_order', 'name'),
            label='Комісія',
        )


class TaskCommentForm(forms.ModelForm):
    class Meta:
        model = TaskComment
        fields = ['body']
        labels = {'body': 'Коментар'}
        widgets = {'body': forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Напишіть, що вже зроблено, які є результати або що заважає…',
        })}
