[![CodeQL](https://github.com/drakeg/tickets/actions/workflows/codeql.yml/badge.svg)](https://github.com/drakeg/tickets/actions/workflows/codeql.yml)

A simpler ServiceNow-style ticketing system.

Includes:
- CMDB
- Project list
- Issue tracker

## Local setup

Install dependencies and run the normal Django setup for the project. Development mode is enabled by default.

Runtime settings can be supplied with environment variables:

- `DJANGO_DEBUG` — defaults to `true`
- `DJANGO_SECRET_KEY` — required when `DJANGO_DEBUG=false`
- `DJANGO_ALLOWED_HOSTS` — comma-separated hostnames, for example `tickets.example.com,localhost`

Create an administrator account with Django's standard command:

```bash
python manage.py createsuperuser
```

Do not use shared or repository-documented default credentials.
