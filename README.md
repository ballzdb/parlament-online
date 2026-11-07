# Парламент.Online

Парламент.Online — платформа для студентського парламенту Харківського університетського ліцею. Вона об’єднує ідеї, голосування, реалізацію рішень і звітність у одному місці.

## Stack
- Python 3.12+
- Django 6.1
- SQLite
- Django templates + HTML/CSS
- Built-in auth and Django admin

## Quick start

### Windows
1. Open PowerShell in the project folder.
2. Create and activate a virtual environment.
3. Install dependencies:
   ```powershell
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```
4. Create a `.env` file from `.env.example` and update values.
5. Run migrations:
   ```powershell
   .\.venv\Scripts\python.exe manage.py migrate
   ```
6. Seed commissions:
   ```powershell
   .\.venv\Scripts\python.exe manage.py seed_commissions
   ```
7. Start the local server:
   ```powershell
   .\.venv\Scripts\python.exe manage.py runserver
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

## Roles
- student
- member
- commission_head
- secretary

## Admin commands
- `python manage.py create_secretary`
- `python manage.py seed_commissions`
- `python manage.py seed_demo_data`

## Tests
```bash
python manage.py test
```

## Deployment notes
This repository is for local development and open-source maintenance. Deploy only after a proper production review, environment configuration and secure settings are prepared.

## Ukrainian note
Ця платформа зроблена для того, щоб учні бачили дорогу від ідеї до результату: ідея → голосування → реалізація → звіт.
