[![CodeQL](https://github.com/drakeg/tickets/actions/workflows/codeql.yml/badge.svg)](https://github.com/drakeg/tickets/actions/workflows/codeql.yml)

A simpler ServiceNow-style ticketing system.

Includes:
- CMDB
- Project list
- Issue tracker
- Knowledge base

## Development standards

Project development follows documented sprint, coding, testing, and pull-request standards:

- [Contributing workflow](CONTRIBUTING.md)
- [Sprint process and history](docs/SPRINTS.md)
- [Coding standards](docs/CODING_STANDARDS.md)
- [Testing standards](docs/TESTING.md)

These documents should be updated alongside the code whenever project workflow, quality gates, or sprint scope changes.

## Local development with Docker Compose

Docker Compose is the recommended way to exercise the application locally.

Start the application:

```bash
docker compose up --build
```

The site is available at `http://localhost:8000` by default.

### Configure ports with a .env file

Copy the included example file:

```bash
cp .env.example .env
```

Then edit `.env`:

```dotenv
APP_PORT=8080
CONTAINER_PORT=8000
```

Docker Compose reads the root `.env` file automatically, so after saving it you can simply run:

```bash
docker compose up --build
```

The local `.env` file is ignored by Git; commit changes to `.env.example` instead when project defaults or supported variables change.

You can also override the values inline. To change only the host port while Django still listens on port 8000 inside the container:

```bash
APP_PORT=8080 docker compose up --build
```

To change the port Django listens on inside the container as well:

```bash
CONTAINER_PORT=9000 APP_PORT=9000 docker compose up --build
```

The two values may differ. For example, this publishes host port 8080 to container port 9000:

```bash
APP_PORT=8080 CONTAINER_PORT=9000 docker compose up --build
```

- `APP_PORT` controls the port exposed on the host and defaults to `8000`.
- `CONTAINER_PORT` controls the port Django listens on inside the container and defaults to `8000`.

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

Python 3.12 or newer is required; Python 3.11 is no longer supported. The test suite runs in GitHub Actions on Python 3.12. CI also checks Django configuration, migration drift, and a Docker Compose smoke build/check.

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
