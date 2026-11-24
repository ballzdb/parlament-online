from __future__ import annotations

import secrets
import logging

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
from .models import AuditLog, PRIMARY_ADMIN_EMAIL, User
from .utils import normalize_email

logger = logging.getLogger(__name__)


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
            if email == PRIMARY_ADMIN_EMAIL:
                form.add_error('email', 'Цей обліковий запис створюється лише через захищену консоль сервера.')
                return render(request, 'accounts/register.html', {'form': form})
            ip_key = f'registration:{request.META.get("REMOTE_ADDR", "unknown")}'
            if cache.get(ip_key, 0) >= 10:
                messages.error(request, 'Занадто багато реєстрацій з цієї IP. Спробуйте пізніше.')
                return render(request, 'accounts/register.html', {'form': form})
            with transaction.atomic():
                existing = User.objects.filter(email__iexact=email).first()
                if existing and existing.is_active:
                    form.add_error('email', 'Користувач з такою поштою вже існує.')
                    return render(request, 'accounts/register.html', {'form': form})
                user = existing or User(email=email)
                user.role = User.Role.STUDENT
                user.additional_roles = []
                user.is_staff = False
                user.is_superuser = False
                user.display_name = form.cleaned_data['display_name'].strip()
                user.grade, user.class_letter = form.cleaned_data['school_class']
                user.set_password(form.cleaned_data['password'])
                user.is_active = True
                user.email_verified_at = None
                user.must_change_password = False
                user.save()
                cache.set(ip_key, cache.get(ip_key, 0) + 1, timeout=60 * 60)
            messages.success(request, 'Обліковий запис створено. Тепер ви можете увійти.')
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
        # Record a failed authentication before adding form errors. Checking
        # for an empty error list afterwards can never work because the error
        # above has already been attached to the form.
        if user is not None and user.is_active and password and not form.is_valid():
            _record_login_failure(request, email)

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


@login_required
def role_management(request):
    if request.user.email.casefold() != PRIMARY_ADMIN_EMAIL:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    role_choices = list(User.Role.choices)
    if request.method == 'POST':
        try:
            target_id = int(request.POST.get('user_id', ''))
        except (TypeError, ValueError):
            target_id = None
        target = User.objects.filter(pk=target_id, is_active=True).first() if target_id else None
        selected_roles = list(dict.fromkeys(request.POST.getlist('roles') or [request.POST.get('role', '')]))
        allowed_roles = {choice.value for choice in User.Role}
        if target is None:
            messages.error(request, 'Активного користувача не знайдено.')
        elif target.email.casefold() == PRIMARY_ADMIN_EMAIL:
            messages.error(request, 'Ролі адміністратора змінювати не можна.')
        elif not selected_roles or any(role not in allowed_roles for role in selected_roles):
            messages.error(request, 'Оберіть щонайменше одну коректну роль.')
        else:
            previous_roles = target.roles_display
            target.role = selected_roles[0]
            target.additional_roles = selected_roles[1:]
            target.is_staff = target.has_role(User.Role.SECRETARY)
            target.is_superuser = False
            target.save(update_fields=['role', 'additional_roles', 'is_staff', 'is_superuser'])
            AuditLog.objects.create(
                action='role_changed', email=target.email, user=target,
                details=f'{previous_roles} -> {target.roles_display}; changed_by={request.user.email}',
            )
            messages.success(request, f'Ролі користувача {target.email} оновлено.')
        return redirect('accounts:role_management')

    users = User.objects.filter(is_active=True).exclude(
        email__iexact=PRIMARY_ADMIN_EMAIL
    ).order_by('grade', 'class_letter', 'email')
    return render(request, 'accounts/role_management.html', {'users': users, 'role_choices': role_choices})
