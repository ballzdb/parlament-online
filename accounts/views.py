from __future__ import annotations

import re
import secrets
import logging
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils import timezone

from app.permissions import requires_roles

from .forms import EmailAuthenticationForm, PasswordChangeForm, RegistrationForm
from .models import AuditLog, EmailVerification, PRIMARY_ADMIN_EMAIL, User
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



def _send_verification_code(user):
    now = timezone.now()
    verification = EmailVerification.objects.filter(user=user).first()
    if verification and now - verification.last_sent_at < timedelta(seconds=60):
        return False, 'Код уже надіслано. Перевірте пошту або зачекайте хвилину перед повторним надсиланням.'

    code = f'{secrets.randbelow(1_000_000):06d}'
    expires_at = now + timedelta(minutes=10)
    if verification:
        verification.code_hash = make_password(code)
        verification.expires_at = expires_at
        verification.attempts_used = 0
        verification.last_sent_at = now
        verification.save(update_fields=['code_hash', 'expires_at', 'attempts_used', 'last_sent_at'])
    else:
        verification = EmailVerification.objects.create(
            user=user,
            code_hash=make_password(code),
            expires_at=expires_at,
            attempts_used=0,
            last_sent_at=now,
        )

    subject = 'Код підтвердження — Парламент.Online'
    message = (
        f'Ваш код підтвердження: {code}\n\n'
        'Код дійсний протягом 10 хвилин. Не повідомляйте його іншим людям. '
        'Якщо ви не реєструвалися на Парламент.Online, просто проігноруйте цей лист.'
    )
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
    except Exception:
        logger.exception('Email verification email delivery failed (user_id=%s)', user.pk)
        verification.delete()
        return False, 'Не вдалося надіслати лист. Спробуйте пізніше або повідомте адміністратора сайту.'
    return True, 'Код підтвердження надіслано на вашу електронну пошту.'


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
                if existing:
                    user = existing
                else:
                    user = User(email=email)
                user.role = User.Role.STUDENT
                user.is_staff = False
                user.is_superuser = False
                user.display_name = form.cleaned_data['display_name'].strip()
                user.grade, user.class_letter = form.cleaned_data['school_class']
                user.set_password(form.cleaned_data['password'])
                user.is_active = False
                user.email_verified_at = None
                user.must_change_password = False
                user.save()
                cache.set(ip_key, cache.get(ip_key, 0) + 1, timeout=60 * 60)

            sent, detail = _send_verification_code(user)
            if not sent and not EmailVerification.objects.filter(user=user).exists():
                form.add_error(None, detail)
                return render(request, 'accounts/register.html', {'form': form})
            request.session['pending_email_verification_user_id'] = user.pk
            if sent:
                messages.success(request, detail)
            else:
                messages.info(request, detail)
            return redirect('accounts:verify_email')
    else:
        form = RegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})



def verify_email_view(request):
    user_id = request.session.get('pending_email_verification_user_id')
    user = User.objects.filter(pk=user_id, is_active=False).first() if user_id else None
    if user is None:
        messages.info(request, 'Спочатку введіть дані для реєстрації.')
        return redirect('accounts:register')

    verification = EmailVerification.objects.filter(user=user).first()
    if request.method == 'POST':
        if request.POST.get('action') == 'resend':
            sent, detail = _send_verification_code(user)
            (messages.success if sent else messages.error)(request, detail)
            return redirect('accounts:verify_email')

        code = (request.POST.get('code') or '').strip()
        if verification is None:
            messages.error(request, 'Код не знайдено. Надішліть новий код.')
        elif verification.attempts_used >= 5:
            messages.error(request, 'Вичерпано кількість спроб. Надішліть новий код пізніше.')
        elif timezone.now() >= verification.expires_at:
            messages.error(request, 'Термін дії коду минув. Надішліть новий код.')
        elif not re.fullmatch(r'[0-9]{6}', code):
            messages.error(request, 'Введіть шестизначний код із листа.')
        elif not check_password(code, verification.code_hash):
            verification.attempts_used += 1
            verification.save(update_fields=['attempts_used'])
            messages.error(request, 'Неправильний код підтвердження.')
        else:
            user.is_active = True
            user.email_verified_at = timezone.now()
            user.save(update_fields=['is_active', 'email_verified_at'])
            verification.delete()
            request.session.pop('pending_email_verification_user_id', None)
            messages.success(request, 'Електронну пошту підтверджено. Тепер ви можете увійти.')
            return redirect('accounts:login')

        return redirect('accounts:verify_email')

    return render(request, 'accounts/verify_email.html', {'email': user.email})


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
        selected_roles = list(dict.fromkeys(request.POST.getlist('roles')))
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
                action='roles_changed',
                email=target.email,
                user=target,
                details=f'{previous_roles} -> {target.roles_display}; changed_by={request.user.email}',
            )
            messages.success(request, f'Ролі користувача {target.email} оновлено.')
        return redirect('accounts:role_management')

    users = User.objects.filter(is_active=True).exclude(
        email__iexact=PRIMARY_ADMIN_EMAIL
    ).order_by('grade', 'class_letter', 'email')
    return render(request, 'accounts/role_management.html', {
        'users': users,
        'role_choices': role_choices,
    })
