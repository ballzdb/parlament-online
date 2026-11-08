#!/usr/bin/env bash
set -eu

python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_commissions
python manage.py runserver 127.0.0.1:8000 --noreload
