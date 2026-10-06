# SupraBrokers RecruTask — Contact Manager

Simple Django + DRF + Bootstrap app for managing contacts (recruitment task).

## Stack
- Django 5.1, Django REST Framework, Bootstrap 5 (CDN)
- Postgres 16 via docker-compose

## Quickstart (Docker)
```bash
cp .env.example .env
docker-compose up --build
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```
App: http://localhost:8000 / Admin: http://localhost:8000/admin/

## Quickstart (local)
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# point DB_HOST to local postgres or use docker db only
python manage.py migrate
python manage.py runserver
```

## Decisions
- Avatars are colored initial circles computed from the name. Photo upload
  was deliberately skipped to keep the code small; it can be added later
  (ImageField + MEDIA + validation + old file cleanup).

## Project status
- [x] #1 Setup base
- [ ] #2 Models
- [ ] #3 List UI
- [ ] #4 Forms + validation
- [ ] #5 REST API
- [ ] #6 CSV import
- [ ] #7 Dashboard
- [ ] #8 Tests
- [ ] #9 Weather + caching [FINAL]
- [ ] #10 Export [FINAL]
- [ ] #11 Auth isolation [FINAL]
