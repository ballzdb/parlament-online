from __future__ import annotations

import random

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils import timezone

from .forms import EmailAuthenticationForm, PasswordChangeForm, RegistrationForm
from .models import User
from .utils import normalize_email


def get_lockout_key(email: str, ip: str) -> str:
    return f'auth_lockout:{email}:{ip}'


def _login_failed_attempts(request, email: str):
    key = get_lockout_key(email, request.META.get('REMOTE_ADDR', 'unknown'))
    return cache.get(key, 0)


def _record_login_failure(request, email: str):
    key = get_lockout_key(email, request.META.get('REMOTE_ADDR', 'unknown'))
    attempts = cache.get(key, 0) + 1
    cache.set(key, attempts, timeout=60 * 15)
    return attempts


def _clear_login_failure(request, email: str):
    cache.delete(get_lockout_key(email, request.META.get('REMOTE_ADDR', 'unknown')))


def _get_login_error_reason(email: str, password: str | None, request) -> str:
    normalized = normalize_email(email)
    if not normalized:
        return 'Немає облікового запису з такою поштою.'
    user = User.objects.filter(email__iexact=normalized).first()
    if user is None:
        return 'Немає облікового запису з такою поштою.'
    if not user.is_active:
        return 'Аккаунт не активований.'
    lockout_key = get_lockout_key(normalized, request.META.get('REMOTE_ADDR', 'unknown'))
    if cache.get(lockout_key, 0) >= 5:
        return 'Аккаунт заблоковано на 15 хвилин.'
    if password is not None and not user.check_password(password):
        return 'Невірний пароль.'
    return 'Невірна пошта або пароль.'


def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            email = normalize_email(form.cleaned_data['email'])
            ip_key = f'registration:{request.META.get("REMOTE_ADDR", "unknown")}'
            if cache.get(ip_key, 0) >= 10:
                messages.error(request, 'Занадто багато реєстрацій з цієї IP. Спробуйте пізніше.')
                return render(request, 'accounts/register.html', {'form': form})
            try:
                with transaction.atomic():
                    existing = User.objects.filter(email__iexact=email).first()
                    if existing and existing.is_active:
                        form.add_error('email', 'Користувач з такою поштою вже існує.')
                        return render(request, 'accounts/register.html', {'form': form})
                    if existing:
                        user = existing
                    else:
                        user = User(email=email)
                    user.role = User.Role.STUDENT
                    user.display_name = (form.cleaned_data.get('display_name') or '').strip() or email.split('@', 1)[0]
                    user.grade = form.cleaned_data.get('grade')
                    user.class_letter = form.cleaned_data.get('class_letter', '')
                    user.set_password(form.cleaned_data['password'])
                    user.is_active = True
                    user.email_verified_at = timezone.now()
                    user.must_change_password = False
                    user.save()
                    cache.set(ip_key, cache.get(ip_key, 0) + 1, timeout=60 * 60)
            except Exception:
                messages.error(request, 'Не вдалося створити обліковий запис. Спробуйте ще раз.')
                return render(request, 'accounts/register.html', {'form': form})
            messages.success(request, 'Реєстрація успішна. Тепер ви можете увійти.')
            return redirect('accounts:login')
    else:
        form = RegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    login_error_reason = None
    form = EmailAuthenticationForm()
    if request.method == 'POST':
        form = EmailAuthenticationForm(request, data=request.POST)
        email = normalize_email(request.POST.get('username', ''))
        password = request.POST.get('password')
        user = User.objects.filter(email__iexact=email).first() if email else None
        ip = request.META.get('REMOTE_ADDR', 'unknown')
        lockout_key = get_lockout_key(email, ip)
        if user is not None and cache.get(lockout_key, 0) >= 5:
            login_error_reason = 'Аккаунт заблоковано на 15 хвилин.'
        elif user is None and email:
            login_error_reason = 'Немає облікового запису з такою поштою.'
        elif user is not None and not user.is_active:
            login_error_reason = 'Аккаунт не активований.'
        elif form.is_valid():
            user = form.get_user()
            if user is not None:
                _clear_login_failure(request, email)
                if getattr(user, 'must_change_password', False):
                    login(request, user)
                    messages.warning(request, 'Спочатку змініть тимчасовий пароль.')
                    return redirect('accounts:profile')
                if form.cleaned_data.get('remember_me'):
                    request.session.set_expiry(60 * 60 * 24 * 30)
                login(request, user)
                user.last_seen_at = timezone.now()
                user.save(update_fields=['last_seen_at'])
                messages.success(request, 'Вітаємо! Ви увійшли в систему.')
                return redirect('home')
        if settings.ENV == 'dev':
            if not login_error_reason:
                login_error_reason = _get_login_error_reason(email, password, request)
        else:
            login_error_reason = 'Невірна пошта або пароль.'
        if login_error_reason:
            if settings.ENV == 'dev':
                form.add_error(None, login_error_reason)
            else:
                form.add_error(None, 'Невірна пошта або пароль.')
        attempts = _login_failed_attempts(request, email) if email else 0
        if user is not None and password and not form.errors:
            attempts = _record_login_failure(request, email)
            if attempts >= 5:
                login_error_reason = 'Невірна пошта або пароль. Обліковий запис заблоковано на 15 хвилин.'
                form.add_error(None, login_error_reason)
            else:
                login_error_reason = 'Невірна пошта або пароль.'
                form.add_error(None, login_error_reason)
    return render(request, 'accounts/login.html', {'form': form, 'login_error_reason': login_error_reason})


def logout_view(request):
    logout(request)
    messages.info(request, 'Ви вийшли з облікового запису.')
    return redirect('home')


def request_password_reset(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        user = User.objects.filter(email=email).first()
        if user and user.is_secretary:
            temp_password = ''.join(random.choice('ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789') for _ in range(12))
            user.set_password(temp_password)
            user.must_change_password = True
            user.save(update_fields=['password', 'must_change_password'])
            messages.success(request, f'Тимчасовий пароль для {user.email}: {temp_password}. Він показаний один раз. Після входу користувач повинен змінити його.')
            return redirect('accounts:login')
        messages.success(request, 'Якщо користувач із такою поштою існує, запит оброблено.')
        return redirect('accounts:login')
    return render(request, 'accounts/reset_request.html')


@login_required
def profile_view(request):
    form = PasswordChangeForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        request.user.set_password(form.cleaned_data['new_password'])
        request.user.must_change_password = False
        request.user.save(update_fields=['password', 'must_change_password'])
        messages.success(request, 'Пароль успішно змінено.')
        return redirect('accounts:profile')
    return render(request, 'accounts/profile.html', {'user': request.user, 'form': form})