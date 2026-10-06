# SupraBrokers RecruTask — Contact Manager

Simple Django + DRF + Bootstrap app for managing contacts (recruitment task).
All code, identifiers and comments are in English.

## Features
- Contact list with search (accent-insensitive), status/city filters,
  sorting (surname / added date) and pagination
- Add / edit / delete contacts (modal forms with client + server validation)
- Contact detail panel loaded on click (no page reload)
- Weather per city (Open-Meteo + Nominatim) with icons, caching and lazy loading
- CSV import with skipped-row reasons and sample file, CSV export (UTF-8 BOM)
- Dashboard with one chart: contacts per city
- Login without registration, users see own or shared contacts only
- Light / dark theme toggle, responsive layout
- REST API: `GET/POST /api/contacts/`, `PUT/DELETE /api/contacts/{id}/`
  (`status` is the status id, `status_name` is the English label)

## Stack
- Django 5.1, Django REST Framework, Bootstrap 5 + Lucide (CDN), vanilla JS
- Postgres 16 via docker-compose

## Quickstart (Docker)
```bash
cp .env.example .env
docker compose up --build -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py seed_contacts --count 20  # demo data
```
App: http://localhost:8000 / Admin: http://localhost:8000/admin/

Note: if port 5432 is taken by a local Postgres, stop it or remap the
`db` ports in `docker-compose.yml`.

## Quickstart (local)
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# point DB_HOST to a running Postgres, then:
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Tests
Tests need a Postgres database (the `unaccent` search uses a Postgres
extension created by migrations; the DB user must be allowed to create
extensions — the compose `postgres` superuser is fine):
```bash
# example against a Postgres on localhost:5433
DB_HOST=localhost DB_PORT=5433 DB_NAME=suprabrokers DB_USER=postgres \
DB_PASSWORD=postgres python manage.py test
```

## Approach and decisions
- Search ignores Polish diacritics and case via the Postgres `unaccent`
  extension (no extra columns, no schema churn; the project is Postgres-only).
- Avatars are colored initial circles derived from the name. Photo upload
  was deliberately skipped to keep the code small; it can be added later
  (ImageField + MEDIA + validation + old file cleanup).
- The UI stays English-only on purpose (recruitment code is English-first);
  status labels are humanized (`in_progress` → `In progress`) from one source.
- Dashboard intentionally has a single chart (contacts per city).
- Weather is fetched once per unique city per page load; coordinates are
  cached 24h, weather 45 min, misses 10 min.
