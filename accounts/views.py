from __future__ import annotations

import secrets
import logging
import hashlib
import html
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.hashers import make_password
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
from .models import AuditLog, EmailVerification, PendingRegistration, PRIMARY_ADMIN_EMAIL, User
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

def _send_verification_email(request, pending, force=False):
    now = timezone.now()
    if not force and pending.last_sent_at > now - timedelta(seconds=VERIFICATION_RESEND_COOLDOWN):
        return False
    token = secrets.token_urlsafe(32)
    pending.token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    pending.expires_at = now + VERIFICATION_LIFETIME
    pending.last_sent_at = now
    pending.save(update_fields=["token_hash", "expires_at", "last_sent_at"])
    verify_url = request.build_absolute_uri(reverse("accounts:verify_email", kwargs={"pending_id": pending.pk, "token": token}))
    safe_email = html.escape(pending.email)
    text_body = f"Підтвердіть пошту для Parlament.Online: {verify_url}\nПосилання діє 30 хвилин."
    html_body = (
        '<div style="font-family:Arial,sans-serif;max-width:560px;margin:auto;color:#172b43">'
        '<h2>Підтвердження електронної пошти</h2>'
        f'<p>Вітаємо, {safe_email}!</p>'
        '<p>Натисніть кнопку, щоб завершити реєстрацію та створити обліковий запис.</p>'
        f'<p><a href="{html.escape(verify_url, quote=True)}">Підтвердити пошту</a></p>'
        '<p>Посилання дійсне 30 хвилин. Якщо ви не реєструвалися, проігноруйте лист.</p></div>'
    )
    message = EmailMultiAlternatives(subject="Підтвердіть електронну пошту — Parlament.Online", body=text_body, from_email=settings.DEFAULT_FROM_EMAIL, to=[pending.email])
    message.attach_alternative(html_body, "text/html")
    message.send()
    return True

def verification_pending(request):
    pending_id = request.session.get("pending_registration_id")
    pending = PendingRegistration.objects.filter(pk=pending_id).first() if pending_id else None
    if pending is None:
        return redirect("accounts:login")
    return render(request, "accounts/verification_pending.html", {"email": pending.email})

def resend_verification_email(request):
    if request.method != "POST":
        return redirect("accounts:verification_pending")
    pending_id = request.session.get("pending_registration_id")
    pending = PendingRegistration.objects.filter(pk=pending_id).first() if pending_id else None
    if pending is None:
        messages.error(request, "Заявку на реєстрацію не знайдено. Зареєструйтеся ще раз.")
        return redirect("accounts:register")
    try:
        sent = _send_verification_email(request, pending)
    except Exception:
        logger.exception("Could not resend email verification")
        messages.error(request, "Не вдалося надіслати лист. Спробуйте пізніше.")
    else:
        if sent:
            messages.success(request, "Лист надіслано.")
        else:
            messages.info(request, "Зачекайте хвилину перед повторним надсиланням.")
    return redirect("accounts:verification_pending")

def verify_email(request, pending_id, token):
    pending = PendingRegistration.objects.filter(pk=pending_id).first()
    supplied_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    if pending is None or pending.expires_at <= timezone.now() or not secrets.compare_digest(pending.token_hash, supplied_hash):
        messages.error(request, "Посилання недійсне або прострочене. Запросіть новий лист.")
        if pending:
            request.session["pending_registration_id"] = pending.pk
            return redirect("accounts:verification_pending")
        return redirect("accounts:register")
    with transaction.atomic():
        if User.objects.filter(email__iexact=pending.email).exists():
            pending.delete()
            messages.error(request, "Обліковий запис із цією поштою вже існує.")
            return redirect("accounts:login")
        user = User(
            email=pending.email, password=pending.password_hash, role=User.Role.STUDENT,
            additional_roles=[], display_name=pending.display_name, grade=pending.grade,
            class_letter=pending.class_letter, is_active=True, email_verified_at=timezone.now(),
            must_change_password=False,
        )
        user.save()
        AuditLog.objects.create(action="email_verified", email=user.email, user=user)
        pending.delete()
    request.session.pop("pending_registration_id", None)
    messages.success(request, "Пошту підтверджено. Обліковий запис створено — тепер можна увійти.")
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
            grade, class_letter = form.cleaned_data['school_class']
            now = timezone.now()
            PendingRegistration.objects.filter(expires_at__lt=now - timedelta(days=1)).delete()
            pending, _ = PendingRegistration.objects.update_or_create(
                email=email,
                defaults={
                    'password_hash': make_password(form.cleaned_data['password']),
                    'display_name': form.cleaned_data['display_name'].strip(),
                    'grade': grade, 'class_letter': class_letter, 'token_hash': '',
                    'expires_at': now, 'last_sent_at': now - timedelta(minutes=2),
                },
            )
            request.session['pending_registration_id'] = pending.pk
            cache.set(ip_key, cache.get(ip_key, 0) + 1, timeout=60 * 60)
            try:
                _send_verification_email(request, pending, force=True)
                messages.success(request, 'Заявку створено. Перевірте пошту: обліковий запис з’явиться лише після підтвердження адреси.')
            except Exception:
                logger.exception('Could not send registration verification email')
                messages.error(request, 'Не вдалося надіслати лист. Спробуйте повторно.')
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
    if request.method == 'POST' and request.POST.get('action') == 'delete_user':
        try:
            target_id = int(request.POST.get('user_id', ''))
        except (TypeError, ValueError):
            target_id = None
        target = User.objects.filter(pk=target_id).first() if target_id else None
        if target is None:
            messages.error(request, 'Користувача не знайдено.')
        elif target.email.casefold() == PRIMARY_ADMIN_EMAIL or target.pk == request.user.pk:
            messages.error(request, 'Цей обліковий запис не можна видалити.')
        else:
            email = target.email
            AuditLog.objects.create(action='user_deleted', email=email, details=f'deleted_by={request.user.email}')
            target.delete()
            messages.success(request, f'Користувача {email} видалено.')
        return redirect('accounts:role_management')
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
