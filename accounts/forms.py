from __future__ import annotations

from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

from .utils import is_allowed_email, normalize_email

User = get_user_model()


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, min_length=8, label='Пароль')
    password_confirm = forms.CharField(widget=forms.PasswordInput, min_length=8, label='Підтвердження пароля')
    consent = forms.BooleanField(label='Погоджуюсь з правилами', required=True)

    class Meta:
        model = User
        fields = ['email', 'display_name', 'grade', 'class_letter', 'password']
        labels = {
            'email': 'Електронна пошта',
            'display_name': 'Ім’я для відображення',
            'grade': 'Клас',
            'class_letter': 'Літера класу',
        }

    def clean_email(self):
        email = normalize_email(self.cleaned_data.get('email'))
        if not is_allowed_email(email):
            raise forms.ValidationError('Реєстрація доступна лише для пошти @khul.ukr.education.')
        return email

    def validate_unique(self):
        email = normalize_email(self.cleaned_data.get('email'))
        if email:
            existing = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).first()
            if existing and not existing.is_active:
                return
        super().validate_unique()
        email = normalize_email(self.cleaned_data.get('email'))
        if email:
            existing = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).first()
            if existing and existing.is_active:
                raise ValidationError({'email': 'Користувач з такою поштою вже існує.'})

    def clean_grade(self):
        grade = self.cleaned_data.get('grade')
        if grade is not None and not 5 <= int(grade) <= 11:
            raise forms.ValidationError('Клас має бути від 5 до 11.')
        return grade

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', 'Паролі не співпадають.')
        if not cleaned_data.get('consent'):
            self.add_error('consent', 'Потрібна згода з правилами.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = normalize_email(user.email)
        user.set_password(self.cleaned_data['password'])
        user.is_active = True
        user.email_verified_at = None
        user.must_change_password = False
        if commit:
            user.save()
        return user


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