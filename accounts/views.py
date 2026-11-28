from __future__ import annotations

import secrets
import logging
import hashlib
import html
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.mail import EmailMultiAlternatives
from django.urls import reverse
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

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




VERIFICATION_LIFETIME = timedelta(minutes=30)
VERIFICATION_RESEND_COOLDOWN = 60


def _send_verification_email(request, user, force=False):
    now = timezone.now()
    verification, _ = EmailVerification.objects.get_or_create(
        user=user,
        defaults={"code_hash": "", "expires_at": now, "last_sent_at": now - timedelta(minutes=2)},
    )
    if not force and verification.last_sent_at > now - timedelta(seconds=VERIFICATION_RESEND_COOLDOWN):
        return False

    token = secrets.token_urlsafe(32)
    verification.code_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    verification.expires_at = now + VERIFICATION_LIFETIME
    verification.last_sent_at = now
    verification.attempts_used = 0
    verification.save(update_fields=["code_hash", "expires_at", "last_sent_at", "attempts_used"])

    verify_url = request.build_absolute_uri(
        reverse("accounts:verify_email", kwargs={"user_id": user.pk, "token": token})
    )
    safe_email = html.escape(user.email)
    text_body = (
        f"Вітаємо! Підтвердіть електронну пошту для Parlament.Online: {verify_url}\n"
        "Посилання дійсне 30 хвилин. Якщо ви не реєструвалися, просто проігноруйте цей лист."
    )
    html_body = (
        '<div style="font-family:Arial,sans-serif;max-width:560px;margin:auto;color:#172b43">'
        '<h2>Підтвердження електронної пошти</h2>'
        f'<p>Вітаємо, {safe_email}!</p>'
        '<p>Натисніть кнопку нижче, щоб підтвердити адресу та активувати доступ до Parlament.Online.</p>'
        f'<p><a href="{html.escape(verify_url, quote=True)}" '
        'style="display:inline-block;padding:12px 20px;background:#174b83;color:#fff;'
        'text-decoration:none;border-radius:8px">Підтвердити пошту</a></p>'
        '<p>Посилання дійсне 30 хвилин. Якщо ви не реєструвалися, проігноруйте цей лист.</p>'
        '</div>'
    )
    message = EmailMultiAlternatives(
        subject="Підтвердіть електронну пошту — Parlament.Online",
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    message.attach_alternative(html_body, "text/html")
    message.send()
    return True


def verification_pending(request):
    user_id = request.session.get("pending_email_verification_user_id")
    user = User.objects.filter(pk=user_id, is_active=True).first() if user_id else None
    if user is None or user.email_verified_at:
        return redirect("accounts:login")
    return render(request, "accounts/verification_pending.html", {"email": user.email})


def resend_verification_email(request):
    if request.method != "POST":
        return redirect("accounts:verification_pending")
    user_id = request.session.get("pending_email_verification_user_id")
    user = User.objects.filter(pk=user_id, is_active=True).first() if user_id else None
    if user is None or user.email_verified_at:
        messages.error(request, "Не вдалося знайти обліковий запис для підтвердження.")
        return redirect("accounts:login")
    try:
        sent = _send_verification_email(request, user)
    except Exception:
        logger.exception("Could not resend email verification")
        messages.error(request, "Не вдалося надіслати лист. Спробуйте пізніше.")
    else:
        if sent:
            messages.success(request, "Лист із посиланням для підтвердження надіслано.")
        else:
            messages.info(request, "Зачекайте хвилину перед повторним надсиланням.")
    return redirect("accounts:verification_pending")


def verify_email(request, user_id, token):
    user = User.objects.filter(pk=user_id, is_active=True).first()
    verification = EmailVerification.objects.filter(user=user).first() if user else None
    supplied_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    if (
        user is None or verification is None or user.email_verified_at
        or verification.expires_at <= timezone.now()
        or not secrets.compare_digest(verification.code_hash, supplied_hash)
    ):
        messages.error(request, "Посилання недійсне або прострочене. Запросіть новий лист.")
        if user and not user.email_verified_at:
            request.session["pending_email_verification_user_id"] = user.pk
            return redirect("accounts:verification_pending")
        return redirect("accounts:login")

    user.email_verified_at = timezone.now()
    user.save(update_fields=["email_verified_at"])
    verification.delete()
    request.session.pop("pending_email_verification_user_id", None)
    AuditLog.objects.create(action="email_verified", email=user.email, user=user)
    messages.success(request, "Електронну пошту підтверджено. Тепер можна увійти.")
    return redirect("accounts:login")


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
            request.session['pending_email_verification_user_id'] = user.pk
            try:
                _send_verification_email(request, user, force=True)
                messages.success(request, 'Обліковий запис створено. Перевірте пошту та натисніть посилання для підтвердження.')
            except Exception:
                logger.exception('Could not send registration verification email')
                messages.error(request, 'Обліковий запис створено, але лист не вдалося надіслати. Спробуйте повторно надіслати його нижче.')
            return redirect('accounts:verification_pending')
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
            if user is not None and not user.email_verified_at:
                request.session['pending_email_verification_user_id'] = user.pk
                messages.warning(request, 'Спочатку підтвердіть електронну пошту.')
                try:
                    _send_verification_email(request, user)
                except Exception:
                    logger.exception('Could not send login verification email')
                    messages.error(request, 'Не вдалося надіслати лист. Скористайтеся повторним надсиланням на сторінці підтвердження.')
                return redirect('accounts:verification_pending')
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
