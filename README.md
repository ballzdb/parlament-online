# Парламент.Online

Парламент.Online — вебплатформа для учнівського парламенту Харківського університетського ліцею. Вона об’єднує шлях учнівської пропозиції від подання й модерації до голосування, організації виконання та звітування.

## Можливості

- реєстрація та вхід за електронною поштою;
- подання учнівських ідей;
- пошук, сортування та посторінкова навігація в каталозі ідей;
- модерація ідей: схвалення або відхилення з фіксацією рішення;
- перемикач української та англійської мов інтерфейсу;
- необов’язкова AI-перевірка ідей на можливі порушення з обов’язковим рішенням людини;
- видалення ідей уповноваженими модераторами та парламентарями;
- тимчасові обмеження для облікових записів із журналюванням дій;
- голосування за опубліковані ідеї;
- публікація заходів та архів подій;
- організаційні завдання, відповідальні й історія змін;
- звернення та апеляції;
- поширені запитання з можливістю редагування через Django Admin;
- статистика й аналітика для уповноважених користувачів;
- підтримка кількох ролей одного користувача;
- адаптивний інтерфейс для комп’ютерів, планшетів і телефонів.

## Технології

- Python;
- Django 6.1;
- Django Templates, HTML і CSS;
- SQLite для локального запуску;
- PostgreSQL для production;
- Gunicorn як WSGI-сервер;
- WhiteNoise для статичних файлів;
- Neon для керованої production-бази даних;
- Render для розгортання вебзастосунку.

## Ролі

Користувач може мати одну або кілька ролей одночасно:

- `student` — учень;
- `member` — парламентарій;
- `moderator` — модератор ідей;
- `commission_head` — голова комісії;
- `secretary` — секретар.

Права перевіряються на сервері. Призначення службових ролей виконує адміністратор. Наявність кількох ролей не надає автоматично прав адміністратора.

## Локальний запуск

### Windows (PowerShell)

1. Відкрийте PowerShell у папці проєкту.
2. Створіть і активуйте віртуальне середовище.
3. Встановіть залежності:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   ```

4. Створіть файл `.env` на основі `.env.example` та налаштуйте локальні значення.
5. Застосуйте міграції й додайте початкові комісії:

   ```powershell
   python manage.py migrate
   python manage.py seed_commissions
   ```

6. Запустіть сервер:

   ```powershell
   python manage.py runserver
   ```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_commissions
python manage.py runserver
```

Без `DATABASE_URL` локальний запуск використовує SQLite. Якщо `DATABASE_URL` задано, застосунок підключається до PostgreSQL.

## English interface and AI screening

The shared interface includes a Ukrainian/English language switch. English translations are being expanded page by page; some user-generated content and less common screens may remain in Ukrainian until translated.

Optional idea screening uses the Gemini API. Set `GEMINI_API_KEY` in `.env` locally or in the Render service environment to enable it. `GEMINI_MODEL` can override the model name. Without a key, or if the provider is unavailable, ideas are still submitted and remain in the ordinary human moderation queue. AI results are advisory only and never publish or reject an idea automatically. Provider free-tier quotas and availability can change; check Google's current Gemini API pricing and limits before relying on it.

## Команди адміністрування

- `python manage.py create_secretary`
- `python manage.py seed_commissions`
- `python manage.py seed_demo_data`

## Тестування

Запуск усіх тестів Django:

```bash
python manage.py test
```

GitHub Actions автоматично виконує перевірку конфігурації Django, перевірку відсутності незгенерованих міграцій і весь набір тестів після push або створення pull request до `main`. Серед регресійних перевірок є контроль прав доступу, унікальності голосів, видалення ідей, роботи з подіями, пошуку та пагінації каталогу.

## Production-розгортання

Production-версія розгортається на Render і використовує PostgreSQL у Neon. Сервіс запускається командою:

```bash
gunicorn config.wsgi:application
```

Команда збірки:

```bash
bash build.sh
```

Сценарій збірки встановлює залежності, збирає статичні файли, застосовує міграції та створює початкові записи комісій.

Для production потрібно налаштувати щонайменше `SECRET_KEY`, `DEBUG=False`, `ENV=prod`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` і `DATABASE_URL`. Секрети не можна зберігати в репозиторії або передавати в публічних повідомленнях.

## Принцип проєкту

Платформа допомагає учням бачити шлях від ідеї до результату:

**ідея → модерація → голосування → реалізація → звіт.**
