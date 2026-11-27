from __future__ import annotations

from django import forms
from django.utils import timezone

from accounts.models import User


REJECTION_CATEGORIES = (
    ('off_topic', 'Не стосується діяльності ліцею або учнівського самоврядування'),
    ('duplicate', 'Дублює вже подану або реалізовану ідею'),
    ('insufficient_detail', 'Недостатньо інформації для розгляду'),
    ('unrealistic', 'Нереалістична пропозиція або немає зрозумілого способу реалізації'),
    ('rule_violation', 'Порушує правила платформи'),
    ('offensive', 'Образливий або неприйнятний зміст'),
    ('personal_data', 'Містить персональні дані або порушує приватність'),
    ('spam', 'Спам, реклама або не є пропозицією'),
    ('other', 'Інша причина'),
)


class IdeaRejectionForm(forms.Form):
    category = forms.ChoiceField(choices=REJECTION_CATEGORIES)
    comment = forms.CharField(
        required=False,
        max_length=500,
        label='Додаткове пояснення (необов’язково)',
        widget=forms.Textarea(attrs={
            'rows': 2,
            'placeholder': 'За бажанням додайте коротке пояснення для автора',
        }),
    )


class TemporaryRestrictionForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True, role=User.Role.STUDENT).order_by('grade', 'class_letter', 'display_name'),
        label='Обліковий запис учня',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        student_ids = [
            user.pk for user in User.objects.filter(is_active=True) if user.is_student
        ]
        self.fields['user'].queryset = User.objects.filter(pk__in=student_ids).order_by(
            'grade', 'class_letter', 'display_name'
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
