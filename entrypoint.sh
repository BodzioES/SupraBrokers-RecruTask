#!/bin/sh
# Production entrypoint: migrate, seed demo data, collect static files,
# then run gunicorn. Fails fast if the database is unreachable.
set -e

python manage.py migrate --noinput
python manage.py seed_contacts --count 20
python manage.py collectstatic --noinput

exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
