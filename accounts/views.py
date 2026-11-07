from __future__ import annotations

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core import signing
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import EmailAuthenticationForm, RegistrationForm
from .models import User


def send_account_email(request, user, subject, action_name, salt):
    token = signing.dumps({'user_id': user.pk, 'email': user.email}, salt=salt)
    link = request.build_absolute_uri(reverse(action_name, args=[token]))
    send_mail(
        subject=subject,
        message=f'Перейдіть за посиланням для підтвердження: {link}',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.role = User.Role.STUDENT
            user.email = user.email.lower()
            user.display_name = user.display_name or user.email.split('@')[0]
            user.save()
            send_account_email(request, user, 'Підтвердження реєстрації', 'accounts:activate', 'activation')
            messages.success(request, 'Реєстрація успішна. Перевірте пошту для підтвердження облікового запису.')
            return redirect('accounts:login')
    else:
        form = RegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = authenticate(request, username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            if user is not None:
                login(request, user)
                user.last_seen_at = timezone.now()
                user.save(update_fields=['last_seen_at'])
                messages.success(request, 'Вітаємо! Ви увійшли в систему.')
                return redirect('home')
            messages.error(request, 'Невірна електронна пошта або пароль.')
    else:
        form = EmailAuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'Ви вийшли з облікового запису.')
    return redirect('home')


def activate_account(request, token):
    try:
        payload = signing.loads(token, salt='activation')
    except signing.BadSignature:
        messages.error(request, 'Посилання недійсне або застаріло.')
        return redirect('accounts:register')

    user = User.objects.filter(pk=payload.get('user_id'), email=payload.get('email')).first()
    if user is None:
        messages.error(request, 'Користувача не знайдено.')
        return redirect('home')

    user.is_active = True
    user.email_verified_at = timezone.now()
    user.save(update_fields=['is_active', 'email_verified_at'])
    messages.success(request, 'Обліковий запис підтверджено. Тепер ви можете увійти.')
    return redirect('accounts:login')


def request_password_reset(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        user = User.objects.filter(email=email).first()
        if user:
            send_account_email(request, user, 'Скидання пароля', 'accounts:reset_password', 'reset')
        messages.success(request, 'Якщо користувач із такою поштою існує, ми надіслали інструкції.')
        return redirect('accounts:login')
    return render(request, 'accounts/reset_request.html')


def reset_password(request, token):
    try:
        payload = signing.loads(token, salt='reset')
    except signing.BadSignature:
        messages.error(request, 'Посилання для скидання пароля недійсне.')
        return redirect('accounts:login')

    user = User.objects.filter(pk=payload.get('user_id'), email=payload.get('email')).first()
    if request.method == 'POST':
        password = request.POST.get('password', '')
        if len(password) < 8:
            messages.error(request, 'Пароль має містити щонайменше 8 символів.')
            return render(request, 'accounts/reset_password.html', {'token': token})
        user.set_password(password)
        user.save(update_fields=['password'])
        messages.success(request, 'Пароль оновлено. Увійдіть з новим паролем.')
        return redirect('accounts:login')

    if user is None:
        messages.error(request, 'Користувача не знайдено.')
        return redirect('accounts:login')
    return render(request, 'accounts/reset_password.html', {'token': token})


@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html', {'user': request.user})
