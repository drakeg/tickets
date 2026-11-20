# Security Policy

## Supported versions

ServDesk has not yet published a versioned stable release. The current
`master` branch is the development line receiving security fixes. No older
versions are promised ongoing support. Once releases are published, supported
versions will be documented here and in `RELEASES.md`.

## Reporting vulnerabilities

Please use [GitHub's private vulnerability reporting](https://github.com/drakeg/tickets/security/advisories/new)
when enabled, or contact the repository maintainer privately using GitHub's
profile contact information. Do not disclose exploit details in a public issue.

Never include production credentials, tokens, personal data, or customer records
in reports. Include reproduction steps, affected revision, and impact with
redacted examples. The maintainer will triage and coordinate disclosure; no
response-time SLA is currently promised.

## Deployment note

Docker Compose defaults to a development Django server and SQLite. It is not
a hardened public production deployment. Use trusted LAN access only for
development; before internet exposure, set `DJANGO_DEBUG=false`, configure a
unique secret and allowed hosts, TLS/reverse proxy, backups, and a supported
production WSGI/ASGI server.
