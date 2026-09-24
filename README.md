[![CodeQL](https://github.com/drakeg/tickets/actions/workflows/codeql.yml/badge.svg)](https://github.com/drakeg/tickets/actions/workflows/codeql.yml)

A simpler ServiceNow-style ticketing system.

Includes:
- CMDB
- Project list
- Issue tracker
- Knowledge base

## Local development with Docker Compose

Docker Compose is the recommended way to exercise the application locally.

Start the application:

```bash
docker compose up --build
```

The site is available at `http://localhost:8000`. To use another host port:

```bash
APP_PORT=8080 docker compose up --build
```

The web service automatically applies migrations before starting Django. Its SQLite database is stored in the named `tickets_data` volume so local data survives container recreation.

Create a local administrator:

```bash
docker compose exec web python manage.py createsuperuser
```

Stop the application:

```bash
docker compose down
```

Remove the local database as well:

```bash
docker compose down -v
```

## Running tests

Run the complete functional Django test suite in an isolated Compose service:

```bash
docker compose run --rm test
```

For a faster targeted run while developing one area:

```bash
docker compose run --rm test python manage.py test issues projects inventory --verbosity 2
```

The same test suite runs in GitHub Actions on Python 3.11 and 3.12. CI also checks Django configuration, migration drift, and a Docker Compose smoke build/check.

## Running without Docker

Install the Python dependencies, apply migrations, then start Django:

```bash
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Runtime settings can be supplied with environment variables:

- `DJANGO_DEBUG` — defaults to `true`
- `DJANGO_SECRET_KEY` — required when `DJANGO_DEBUG=false`
- `DJANGO_ALLOWED_HOSTS` — comma-separated hostnames, for example `tickets.example.com,localhost`
- `DJANGO_DB_PATH` — optional SQLite database location; defaults to `db.sqlite3` in the project root

Create an administrator with:

```bash
python manage.py createsuperuser
```

Do not use shared or repository-documented default credentials.
