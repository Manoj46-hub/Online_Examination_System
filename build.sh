#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input

python manage.py migrate

if ! python manage.py shell -c "import os, sys; from django.contrib.auth import get_user_model; User = get_user_model(); exists = User.objects.filter(**{User.USERNAME_FIELD: os.environ['DJANGO_SUPERUSER_USERNAME']}).exists(); sys.exit(0 if exists else 1)"; then
    python manage.py createsuperuser --noinput
fi