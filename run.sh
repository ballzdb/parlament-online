#!/usr/bin/env bash
set -eu

if [ ! -f .env ]; then
  umask 077
  secret_key="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
  printf 'SECRET_KEY=%s\nDEBUG=True\nALLOWED_HOSTS=localhost,127.0.0.1\n' "$secret_key" > .env
  printf 'Created local .env with a generated SECRET_KEY.\n'
fi

python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_commissions
python manage.py runserver 127.0.0.1:8000 --noreload
