# Налаштування Gmail SMTP для Парламент.Online

Цей документ пояснює, як підключити Gmail SMTP без зберігання паролів у репозиторії.

## 1. Створіть окремий Gmail-аккаунт

- Створіть окремий поштовий ящик для сервера, наприклад `parlament-online-noreply@gmail.com`.
- Увімкніть двофакторну автентифікацію.
- Згенеруйте пароль застосунку:
  - Увійдіть в Google Account → Security → App passwords
  - Виберіть "Mail" і "Windows Computer"
  - Скопіюйте згенерований 16-символьний пароль

## 2. Додайте змінні середовища на сервері

У `.env` запишіть:

```env
ENV=prod
EMAIL_BACKEND=smtp
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=parlament-online-noreply@gmail.com
EMAIL_HOST_PASSWORD=your-16-char-app-password
DEFAULT_FROM_EMAIL=Парламент ліцею <parlament-online-noreply@gmail.com>
SECRETARY_EMAIL=secretary@your-school.example
BASE_URL=https://your-domain.example
```

Не додавайте `.env` до Git. Відкрийте права доступу:

```bash
chmod 600 .env
```

## 3. Перевірка відправки

Після перезапуску Django виконайте:

```bash
python -m app.cli test-email your-test@example.com
python manage.py send_queued_emails
```

Якщо лист прийшов, налаштування успішні.

## 4. Ключові обмеження Gmail

- Gmail не рекомендує використовувати SMTP для масової розсилки.
- Для реальних розсилок краще використовувати SendGrid, Resend або Postmark.
- Для 24/7 автоматичних листів використовуйте окремий поштовий аккаунт і не надсилайте масові листи з одного особистого ящика.

## 5. Рекомендація по домену

Для правильного `From` і нудного спаму краще використовувати домен `@your-school.example` або корпоративний домен з підтвердженим DKIM.
