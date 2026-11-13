from __future__ import annotations

import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from app.permissions import requires_roles

from .forms import EmailAuthenticationForm, PasswordChangeForm, RegistrationForm
from .models import AuditLog, User
from .utils import normalize_email


LOGIN_FAILURE_ACTION = 'login_failed'
LOGIN_FAILURE_LIMIT = 5
LOGIN_FAILURE_WINDOW = timedelta(minutes=15)


def _login_failed_attempts(email: str, ip: str) -> int:
    cutoff = timezone.now() - LOGIN_FAILURE_WINDOW
    AuditLog.objects.filter(
        action=LOGIN_FAILURE_ACTION,
        created_at__lt=cutoff,
    ).delete()
    return AuditLog.objects.filter(
        action=LOGIN_FAILURE_ACTION,
        email=email,
        details=ip,
        created_at__gte=cutoff,
    ).count()


def _record_login_failure(email: str, ip: str, user: User | None) -> int:
    with transaction.atomic():
        AuditLog.objects.create(
            action=LOGIN_FAILURE_ACTION,
            email=email,
            details=ip,
            user=user,
        )
        return _login_failed_attempts(email, ip)


def _clear_login_failures(email: str, ip: str) -> None:
    AuditLog.objects.filter(
        action=LOGIN_FAILURE_ACTION,
        email=email,
        details=ip,
    ).delete()


def _get_login_error_reason(email: str, password: str | None) -> str:
    normalized = normalize_email(email)
    if not normalized:
        return 'Немає облікового запису з такою поштою.'
    user = User.objects.filter(email__iexact=normalized).first()
    if user is None:
        return 'Немає облікового запису з такою поштою.'
    if not user.is_active:
        return 'Аккаунт не активований.'
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
                user.display_name = form.cleaned_data['display_name'].strip()
                user.grade, user.class_letter = form.cleaned_data['school_class']
                user.set_password(form.cleaned_data['password'])
                user.is_active = True
                user.must_change_password = False
                user.save()
                cache.set(ip_key, cache.get(ip_key, 0) + 1, timeout=60 * 60)
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
        if email and _login_failed_attempts(email, ip) >= LOGIN_FAILURE_LIMIT:
            login_error_reason = 'Аккаунт заблоковано на 15 хвилин.'
            form.add_error(None, login_error_reason)
            return render(request, 'accounts/login.html', {
                'form': form,
                'login_error_reason': login_error_reason,
            })
        elif user is None and email:
            login_error_reason = 'Немає облікового запису з такою поштою.'
        elif user is not None and not user.is_active:
            login_error_reason = 'Аккаунт не активований.'
        elif form.is_valid():
            user = form.get_user()
            if user is not None:
                _clear_login_failures(email, ip)
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
                login_error_reason = _get_login_error_reason(email, password)
        else:
            login_error_reason = 'Невірна пошта або пароль.'
        if login_error_reason:
            if settings.ENV == 'dev':
                form.add_error(None, login_error_reason)
            else:
                form.add_error(None, 'Невірна пошта або пароль.')
        if email and password:
            attempts = _record_login_failure(email, ip, user)
            if attempts >= LOGIN_FAILURE_LIMIT:
                login_error_reason = 'Аккаунт заблоковано на 15 хвилин.'
                form.add_error(None, login_error_reason)
    return render(request, 'accounts/login.html', {'form': form, 'login_error_reason': login_error_reason})


@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, 'Ви вийшли з облікового запису.')
    return redirect('home')


@login_required
@requires_roles(User.Role.SECRETARY)
def request_password_reset(request):
    if request.method == 'POST':
        email = normalize_email(request.POST.get('email'))
        user = User.objects.filter(email__iexact=email).first()
        if user:
            temp_password = ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789') for _ in range(12))
            with transaction.atomic():
                user.set_password(temp_password)
                user.must_change_password = True
                user.save(update_fields=['password', 'must_change_password'])
                AuditLog.objects.create(action='password_reset', email=user.email, user=user)
            messages.success(request, f'Тимчасовий пароль для {user.email}: {temp_password}. Передайте його користувачу особисто. Під час наступного входу пароль потрібно змінити.')
        else:
            messages.error(request, 'Користувача з такою поштою не знайдено.')
        return redirect('accounts:reset_request')
    return render(request, 'accounts/reset_request.html')


@login_required
def profile_view(request):
    form = PasswordChangeForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        request.user.set_password(form.cleaned_data['new_password'])
        request.user.must_change_password = False
        request.user.save(update_fields=['password', 'must_change_password'])
        update_session_auth_hash(request, request.user)
        messages.success(request, 'Пароль успішно змінено.')
        return redirect('accounts:profile')
    return render(request, 'accounts/profile.html', {'user': request.user, 'form': form})