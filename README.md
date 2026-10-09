# SupraBrokers RecruTask — Contact Manager

Simple Django + DRF + Bootstrap web app for managing contacts.
Recruitment task: working, readable solution, not production perfection.
All code, identifiers and comments are in English.

## Features
- Contact list with accent-insensitive search, sorting (surname / added date)
  and pagination, plus a click-to-open detail panel (no page reload)
- Add / edit / delete contacts via modal forms with client + server validation
- Weather per city (Open-Meteo + Nominatim) with lazy loading and caching;
  failed lookups never break the page
- CSV import with a skipped-row report and a sample file, CSV export (UTF-8 BOM)
- Dashboard with two charts: contacts per city and contacts per status
- Login without registration; users see and manage only own or shared contacts
- Light / dark theme toggle, responsive layout (on mobile the detail panel
  takes the full width with a Back button, user menu sits in the navbar
  burger), human-readable status labels
- REST API with browsable docs at `/api/docs/`

## Screenshots
> Placeholders — replace with real screenshots before sending.
- `docs/screenshot-list.png` — contact list with detail panel
- `docs/screenshot-form.png` — add/edit modal with validation
- `docs/screenshot-dashboard.png` — charts

## Local installation step by step
```bash
python -m venv .venv
.venv\Scripts\activate        # Windows; Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then point DB_HOST at a running Postgres
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_contacts --count 20   # optional demo data
python manage.py runserver
```
App: http://127.0.0.1:8000/ — log in with the superuser account.

## Docker instructions
```bash
cp .env.example .env
docker compose up --build -d
```
The entrypoint runs migrations, seeds 20 demo contacts and collects static
files, then starts gunicorn (3 workers). App: http://localhost:8000/

Optional Redis cache:
```bash
docker compose --profile redis up -d
# and set REDIS_URL=redis://redis:6379/0 in .env
```

Note: if port 5432 is taken by a local Postgres, stop it or remap the
`db` ports in `docker-compose.yml`.

## Environment variables
| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | dev-only key | Django secret key |
| `DEBUG` | `True` | Debug mode |
| `ALLOWED_HOSTS` | (empty) | Comma-separated hosts |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` / `DB_HOST` / `DB_PORT` | `suprabrokers` / `postgres` / `postgres` / `localhost` / `5432` | Postgres connection |
| `REDIS_URL` | (empty) | e.g. `redis://redis:6379/0`; without it local-memory cache is used |
| `WEATHER_USER_AGENT` | `SupraBrokersRecruTask/1.0 (recruitment task)` | Required by Nominatim |
| `WEATHER_HTTP_TIMEOUT` | `8` | Seconds for weather HTTP calls |

## How to run tests
Tests need a Postgres database (search uses the `unaccent` extension, which
migrations create; the DB user must be allowed to create extensions):
```bash
DB_HOST=localhost DB_PORT=5433 DB_NAME=suprabrokers DB_USER=postgres \
DB_PASSWORD=postgres python manage.py test
```
3 tests (as suggested in the task): model validation (unique phone),
API CRUD (create/update/delete) and CSV import with a skipped-row report.

## Demo credentials
No demo account is shipped. Create one with `createsuperuser` (local) or:
```bash
docker compose exec web python manage.py createsuperuser
```
Then optionally `seed_contacts --count 20` for demo data. Seeded contacts
belong to the `test` user when it exists, otherwise they are shared.

## API examples
The API uses session authentication — log in via the browser first, or reuse
the session cookie. Interactive docs: `/api/docs/`.

```bash
BASE=http://localhost:8000
# list (plain JSON array; ?page=1 / ?page_size=20 enables pagination)
curl -s -b cookies.txt -c cookies.txt $BASE/api/contacts/ | head -c 300
# create (status accepts an id or a name)
curl -s -b cookies.txt -c cookies.txt -X POST $BASE/api/contacts/ \
  -H 'Content-Type: application/json' \
  -d '{"first_name":"Ada","last_name":"Nowak","phone":"600100200","email":"ada@example.com","city":"Warszawa","status":"new"}'
# update
curl -s -b cookies.txt -c cookies.txt -X PUT $BASE/api/contacts/1/ \
  -H 'Content-Type: application/json' \
  -d '{"first_name":"Ada","last_name":"Nowak","phone":"600100200","email":"ada@example.com","city":"Sopot","status":1}'
# delete
curl -s -b cookies.txt -c cookies.txt -X DELETE $BASE/api/contacts/1/ -i | head -1
```
Login via curl: fetch `/accounts/login/` for the CSRF cookie, then POST
`username`, `password` and `csrfmiddlewaretoken` with `-b/-c cookies.txt`.

## Approach and decisions
- **Status as ForeignKey** to a separate table, so values change without code.
- **DRF** for the API (router + ViewSet) instead of hand-rolled JsonResponse.
- **Optional API pagination**: plain array by default (per spec), wrapper only
  with `?page=` / `?page_size=`; the HTML UI stays paginated.
- **Data isolation**: one `visible_contacts()` helper shared by UI and API
  (own + shared, superuser sees all); invisible objects 404.
- **Caching**: coordinates 30 days, weather 45 min (LocMem, Redis via
  `REDIS_URL`); frontend fetches once per unique city per page load.
- **Search** ignores Polish diacritics via the Postgres `unaccent` extension
  (project is Postgres-only, no extra columns needed).
- **Avatars** are colored initial circles; photo upload was deliberately
  skipped to keep the code small.
- UI stays English-only; dashboard has exactly the charts the task needs.

## Possible next steps
- Photo upload for contacts (ImageField + validation + cleanup)
- Full PL/EN language switch
- E-mail notifications or contact activity log
- Production hardening (Sentry, real backups, CI pipeline)
