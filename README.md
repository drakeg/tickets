# ServDesk — SMB Service Desk

<!-- madmallard-badges:start -->
[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)](https://github.com/drakeg/tickets/blob/master/.github/workflows/django-ci.yml) [![Django](https://img.shields.io/badge/Django-6.1-092E20?logo=django&logoColor=white)](https://github.com/drakeg/tickets/blob/master/requirements.txt) [![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3.3-7952B3?logo=bootstrap&logoColor=white)](https://github.com/drakeg/tickets/tree/master/static/tickets) [![SQLite](https://img.shields.io/badge/SQLite-local%20database-003B57?logo=sqlite&logoColor=white)](https://github.com/drakeg/tickets/blob/master/docker-compose.yml) [![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://github.com/drakeg/tickets/blob/master/docker-compose.yml)

[![Django CI](https://github.com/drakeg/tickets/actions/workflows/django-ci.yml/badge.svg)](https://github.com/drakeg/tickets/actions/workflows/django-ci.yml) [![CodeQL](https://github.com/drakeg/tickets/actions/workflows/codeql.yml/badge.svg)](https://github.com/drakeg/tickets/actions/workflows/codeql.yml) [![Issues](https://img.shields.io/github/issues/drakeg/tickets)](https://github.com/drakeg/tickets/issues) [![Pull requests](https://img.shields.io/github/issues-pr/drakeg/tickets)](https://github.com/drakeg/tickets/pulls) [![License](https://img.shields.io/github/license/drakeg/tickets)](https://github.com/drakeg/tickets/blob/master/LICENSE)
<!-- madmallard-badges:end -->

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

## Share a ticket solution

Authorized technicians can choose **Create knowledge article** on saved ticket
details or the ticket update form. The title, complete issue description and
keywords are prefilled. Add the tested solution, remove sensitive details, and
review before publishing. Save any pending ticket edits before leaving its form.

Publishing records the technician as author and links the article to the ticket;
repeated clicks open the existing article. The ticket itself is not changed or
closed. Issue/solution content is searchable and remains available if the source
ticket is later deleted. Permission requires both `issues.view_issue` and
`knowledgebase.add_article`. Knowledge article access follows the module view permissions; review grants before publishing.

## Knowledge base browsing

The knowledge-base list and article search show 15 results per page, newest first.
Use Previous/Next to reach older articles; search phrases remain applied while
paging. Search matches description, keywords, or author. Empty searches show no
results. Existing author/staff editing and authenticated creation remain available.

## Auditing existing asset names

After deploying, administrators can use a **read-only** command to review
historical asset-name problems without changing existing records:

```bash
docker compose exec -T web python manage.py audit_asset_names
# To see affected record IDs for manual review (names remain hidden):
docker compose exec -T web python manage.py audit_asset_names --show-record-ids
```

The command reports empty names, names with surrounding whitespace, and
case-insensitive duplicate system names within one cluster. It does not
remove or rename existing assets. The Django admin system editor also checks
new names for same-cluster duplicates while preserving unrelated edits to
legacy records. An optional `--fail-on-issues` flag returns
an error status for explicit maintenance checks; it is not part of application
startup. Review existing records before considering a uniqueness migration.

## Inventory browsing

System lists and system-name search show 15 records per page, grouped by cluster
and ordered by system name and ID within each cluster. Previous/Next retains
search text. Each row shows its cluster, vendor and operating system, with a link
to the system details and an Add system action above the list.

## Adding systems

System creation requires an operating system, vendor, and cluster. Names must
not be blank or duplicate an existing system in the same cluster (case-insensitive);
leading and trailing spaces are removed. Different clusters may share a name. If a choice
list is empty, the form explains which reference data an administrator must add.
Authorized staff see links to the corresponding Django admin forms. Inventory
creation requires the system add/view grants and view grants for all three
reference lists; vendor creation uses add/view permissions rather than staff alone. Successful
creation redirects to the system details showing all selections and creation date;
refreshing that page does not resubmit the form. Invalid input retains its errors.

## Project browsing

All projects, My projects, Unassigned projects, and project searches show 15
records per page, newest first. Previous/Next preserves the queue and search
phrase. Lists show project summaries, assignments, and optional schedule dates;
projects do not yet have an open/closed lifecycle status.

## Project creation

Creating a project redirects to its detail page; refreshing that page does not
resubmit the form. Details include summary, description, requestor, assignment,
creation date and optional schedule dates. Unassigned/unscheduled fields are
labeled explicitly. Native date controls support schedule entry. If both dates
are supplied, the end date must be on or after the start date. Same-day projects
and partial or blank schedules are supported. Invalid submissions retain values
and validation errors.

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
startup). Existing tickets start with no recorded changes. History covers the application triage form and individual Django admin edits;
raw shell/ORM updates bypass this history. Audited bulk close/reopen status actions are available in Django admin (#217). Deleting a ticket deletes its history. History is an operational record,
not a tamper-proof audit ledger. SQLite does not provide row locks; deployments
requiring concurrent write serialization should use a database with row locking.

## Development standards

Project development follows documented sprint, coding, testing, and pull-request standards:

- [Agent instructions](AGENTS.md)
- [Contributing workflow](CONTRIBUTING.md)
- [Release policy](RELEASES.md)
- [Prioritized product backlog](docs/BACKLOG.md)
- [Detailed sprint delivery plan](docs/SPRINT_PLAN.md)
- [Sprint process and history](docs/SPRINTS.md)
- [Coding standards](docs/CODING_STANDARDS.md)
- [Testing standards](docs/TESTING.md)\n- [SQLite backup and isolated Django recovery rehearsal](docs/BACKUP_RESTORE.md)
- [SMB demo and pilot workflow](docs/SMB_DEMO.md)

These documents should be updated alongside the code whenever project workflow, quality gates, or sprint scope changes.

## Local development with Docker Compose

Docker Compose is the recommended way to exercise the application locally.

Start the application:

```bash
docker compose up --build
```

The site is available at `http://localhost:8000` by default. For LAN testing,
set `DJANGO_ALLOWED_HOSTS` to include the machine's LAN IP or hostname and use
`http://<host-LAN-IP>:<APP_PORT>` from another device. Docker publishes to all
interfaces by default; restrict access using host firewall rules and use a
strong, unique secret outside an isolated test network.

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

- `DJANGO_ALLOWED_HOSTS` defines the accepted hostnames/IPs in Compose (comma-separated).

The two port values may differ. For example, this publishes host port 8080 to container port 9000:

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

## Team roles

Infrastructure Team, Help Desk, and Project Manager defaults can be provisioned
with `docker compose exec web python manage.py setup_roles` after migrations.
Use `--dry-run` to preview. Assign users deliberately through Django admin.
See [role matrix and enforcement plan](docs/ROLES.md): these groups currently
supply native Django grants and existing ticket-triage access. Inventory routes now enforce those permissions, including dashboard/navigation
visibility. Infrastructure members can create inventory without staff access;
Help Desk can read it. Global search returns only authorized models. Remaining
module routes/counters are the next P1 increment; this is not yet full app RBAC.

## Administration appearance

Django admin uses the ServDesk workspace branding, palette and panel styling,
with a Back to workspace link. Native forms, model permissions, actions, theme
switching and responsive navigation remain available. The Priority model's plural
label is explicitly set to Priorities. Apply migrations on upgrade; the label
migration changes Django model options without altering saved records.


### Concurrent system creation and legacy compatibility

New systems created through the application or Django admin receive a hidden,
canonical identity key based on their cluster and whitespace-trimmed,
case-insensitive name. A unique database index prevents two simultaneously
validated forms from saving the same new identity. The additive migration leaves
historical records unchanged (NULL keys), even if duplicate identifiers exist.
Those records remain editable without changing their identity. The read-only
`audit_asset_names` command identifies historical problems for operator review.

This protects the supported web/admin form paths; direct ORM creation, custom
imports or SQL writes need their own validation and identity-key handling.
Do not backfill legacy rows or enforce global uniqueness without first reviewing
the historical audit and migration impact.


When two operators submit the same new system name concurrently, the database
rejects the second insert. The regular system form shows an inline retry
message; Django admin returns to the form with an error message. Unrelated
database integrity errors are not suppressed.


## Finding systems by any inventory field

The Systems search accepts partial, case-insensitive matches against system
names, vendors, operating systems and cluster names. Results are paginated,
ordered deterministically and accessible only to permitted inventory readers.


## Finding tickets by staff, requester or priority

Use the ticket search box to find records by summary, description, requester
name, assigned staff username or priority label. Status filtering remains
available alongside searches, and access stays restricted to authorized readers.


### Docker build cache

Local builds use Docker BuildKit's cache for pip downloads. Rebuild with
`docker compose build web` (or the existing Compose command); dependencies
are still installed from `requirements.txt`. The downloaded wheel cache lives
in the Docker builder rather than inside the app image or persistent SQLite
volume. CI continues to build and smoke-test the image. No speedup is claimed
without timing measurements from the same machine.


### Export ticket queues

From any ticket queue or ticket search, use **Export CSV** to download all
matching tickets (not just the visible page) with the current status, priority,
assignee and search filters applied. Export requires the same ticket-view
permission as the queue. CSV includes ticket descriptions and requester names,
so store files securely and share only with authorized recipients. Potential
spreadsheet formulas in user-supplied fields are prefixed to prevent execution
when opened in spreadsheet applications. This action does not modify tickets.


### Ticket queue ordering

Use the **Order** selector to choose newest-first (default) or oldest-first
when triaging aging requests. Current priority, status, assignee and search
filters continue to apply. The CSV export uses the same ordering as the queue.


### Quick ticket status actions

Agents with ticket-view and ticket-change permissions can close or reopen a
ticket directly from its queue row. These are CSRF-protected POST actions and
create the same actor-attributed triage history as regular ticket editing. They
redirect to ticket detail for confirmation, and users with read-only access do
not see the action buttons. Repeated identical actions do not create duplicate
history events.


### Download change history

Authorized ticket editors can use **Export change history CSV** on a ticket's
detail page to download its before/after status, priority, assignment, actor
and timestamp. The export includes only that ticket and is not offered to
read-only ticket viewers. Store exported audit files securely. This feature
does not determine a retention period or delete historical events.


### Claim an unassigned ticket

Authorized ticket editors can select **Claim** beside an open, unassigned
ticket to assign it to themselves. The change is captured in ticket history.
If it has already been assigned or closed, the request returns a conflict and
does not overwrite the current owner. Claiming uses a protected POST; read-only
users never see the control.


### Return an owned ticket to the queue

An agent can select **Release** for an open ticket currently assigned to
themself, returning it to the unassigned queue. Other agents cannot release
someone else's ticket through this action. Every successful change is audited
and repeated release attempts do not create extra history.


The ticket detail page also provides **Claim this ticket** or **Release my
ticket** when the current agent is authorized and the ticket's ownership and
status allow it. These use the same audited controls as the queue.


### Aging open ticket triage

Select **Open ticket age** on a queue to see tickets that have been open
longer than 24 hours, 3 days or 7 days, measured from their creation date.
Closed tickets are excluded when a threshold is active. Existing search,
priority, owner and sort filters continue to apply; CSV exports reflect the
same selection. This is an age-based triage aid, **not** an SLA or overdue
breach calculation.


### Aging ticket dashboard

Users with permission to view tickets see a dashboard card with the number
of open tickets older than 3 days and a secondary count older than 7 days.
The card links to the same filtered queue, preserving authorization. Counts
reflect ticket creation age and do not represent a contractual SLA breach.


The dashboard also shows **Unassigned open tickets** to ticket readers,
with a direct link to the open, unassigned queue where authorized agents
can claim work. Closed and assigned tickets do not contribute.
