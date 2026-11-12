[![CodeQL](https://github.com/drakeg/tickets/actions/workflows/codeql.yml/badge.svg)](https://github.com/drakeg/tickets/actions/workflows/codeql.yml)

A simpler ServiceNow-style ticketing system.

Includes:
- CMDB
- Project list
- Issue tracker
- Knowledge base

## Workspace navigation

Use the sidebar for Tickets, Projects, Systems and Knowledge base. Quick Create
links and dashboard action cards open each creation form directly. Signed-out
visitors are prompted to sign in before saving records. On narrow screens,
navigation wraps above the content. The workspace styling is served locally and
navigation works without JavaScript.

## Knowledge base browsing

The knowledge-base list and article search show 15 results per page, newest first.
Use Previous/Next to reach older articles; search phrases remain applied while
paging. Search matches description, keywords, or author. Empty searches show no
results. Existing author/staff editing and authenticated creation remain available.

## Project creation

Creating a project redirects to its detail page; refreshing that page does not
resubmit the form. Details include summary, description, requestor, assignment,
creation date and optional schedule dates. Unassigned/unscheduled fields are
labeled explicitly. Invalid submissions retain values and validation errors.

## Ticket workflow

Signed-in users can submit a ticket from **Issues → Create New**. Successful
submissions redirect to the saved ticket, so refreshing the resulting page does
not resubmit the form. Invalid submissions retain the entered values and show
validation errors.

Ticket queues show 15 tickets per page, newest first, with All/Open/Closed status
filters. Search and assignment filters persist while paging. Use **Issues → All
tickets** or **Issues → Closed tickets** to browse the corresponding queue.

Ticket details show the summary, description, status, priority, requestor,
assignee (or Unassigned), and date opened, with a link back to the issue list.

### Agent permissions and ticket updates

Administrators can grant **Issues → issue → Can change issue** to users or groups
in Django admin. This `issues.change_issue` permission allows updating status,
priority, and assignment through **Update ticket** on the detail page. Superusers
also have access; staff status or ticket assignment alone does not grant access.
The permission applies to all tickets, so grant it only to trusted triage agents.

The update form supports closing, reopening, reassignment, and clearing assignment.
Saving redirects to the detail page; Cancel leaves the ticket unchanged. Requestor,
summary, description, and creation date are preserved. Changes require a valid
CSRF-protected POST. Users with `issues.change_issue` can also see paginated change history on ticket
details. Each successful triage change records the actor, timestamp, and before/after
status, priority, and assignment. Unchanged saves create no entry. Ticket updates
and history writes commit together. Actor and field names are snapshots, so later
renames do not rewrite the record; deleted actors retain their recorded name.

Run `python manage.py migrate` when upgrading (Compose applies migrations on
startup). Existing tickets start with no recorded changes. History covers the
application triage form; direct admin, shell, or bulk ORM updates are outside this
increment. Deleting a ticket deletes its history. History is an operational record,
not a tamper-proof audit ledger. SQLite does not provide row locks; deployments
requiring concurrent write serialization should use a database with row locking.

## Development standards

Project development follows documented sprint, coding, testing, and pull-request standards:

- [Contributing workflow](CONTRIBUTING.md)
- [Prioritized product backlog](docs/BACKLOG.md)
- [Detailed sprint delivery plan](docs/SPRINT_PLAN.md)
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
