from __future__ import annotations

import re

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm

from .models import User
from .utils import is_allowed_email, normalize_email


class RegistrationForm(forms.Form):
    email = forms.EmailField(label='Електронна пошта')
    password = forms.CharField(
        widget=forms.PasswordInput(),
        min_length=8,
        label='Пароль',
    )
    display_name = forms.CharField(max_length=120, label='Ім’я')
    school_class = forms.CharField(max_length=12, label='Клас', help_text='Наприклад, 9-А')

    def clean_email(self):
        email = normalize_email(self.cleaned_data.get('email'))
        if not is_allowed_email(email):
            raise forms.ValidationError('Реєстрація доступна лише для пошти @khul.ukr.education.')
        if User.objects.filter(email__iexact=email, is_active=True).exists():
            raise forms.ValidationError('Користувач з такою поштою вже існує.')
        return email

    def clean_school_class(self):
        value = self.cleaned_data['school_class'].replace(' ', '')
        match = re.fullmatch(r'(5|6|7|8|9|10|11)(?:-?([A-Za-zА-Яа-яІіЇїЄєҐґ]))?', value)
        if not match:
            raise forms.ValidationError('Вкажіть клас від 5 до 11, наприклад 9-А.')
        return int(match.group(1)), (match.group(2) or '').upper()


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label='Електронна пошта')
    remember_me = forms.BooleanField(label='Запам’ятати мене на 30 днів', required=False)

    error_messages = {
        **AuthenticationForm.error_messages,
        'invalid_login': 'Невірна пошта або пароль.',
        'inactive': 'Цей обліковий запис неактивний.',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'autocomplete': 'email'})
        self.fields['password'].widget.attrs.update({'autocomplete': 'current-password'})

    def clean(self):
        cleaned_data = super().clean()
        username = normalize_email(cleaned_data.get('username'))
        password = cleaned_data.get('password')
        if username and password:
            self.cleaned_data['username'] = username
            self.user_cache = authenticate(self.request, username=username, password=password)
            if self.user_cache is None:
                raise forms.ValidationError(self.error_messages['invalid_login'], code='invalid_login')
        return cleaned_data


class PasswordChangeForm(forms.Form):
    new_password = forms.CharField(widget=forms.PasswordInput, min_length=8, label='Новий пароль')
    new_password_confirm = forms.CharField(widget=forms.PasswordInput, min_length=8, label='Підтвердження нового пароля')

    def clean(self):
        data = super().clean()
        new_password = data.get('new_password')
        confirm = data.get('new_password_confirm')
        if new_password and confirm and new_password != confirm:
            self.add_error('new_password_confirm', 'Паролі не співпадають.')
        return data
