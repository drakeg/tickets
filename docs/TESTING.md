# Testing Standards

The test suite is intended to provide fast confidence in application behavior while remaining practical for local development.

## Test layers

### Django system checks

Run:

```bash
python manage.py check
```

This catches configuration and framework integration problems.

### Migration drift

Run:

```bash
python manage.py makemigrations --check --dry-run
```

No pull request should introduce unintended migration drift.

### Functional request tests

Use Django's test client for most application workflows. These tests should verify meaningful behavior, not only status code 200.

Examples include:

- authentication and authorization;
- create/detail/list/search flows;
- assignment filtering;
- aggregate dashboard metrics;
- empty/error paths;
- persisted model changes.

Prefer a small number of high-value assertions over brittle checks of every HTML detail.

### Model tests

Add model tests when behavior lives on the model or when validation, defaults, constraints, or helper methods need direct verification.

### Browser/end-to-end tests

Do not add browser automation by default. Introduce it only for workflows that cannot be adequately protected with Django request tests, such as complex client-side interactions.

## Local test commands

Full suite with Docker Compose:

```bash
docker compose run --rm test
```

Targeted app tests:

```bash
docker compose run --rm test python manage.py test issues projects inventory --verbosity 2
```

Without Docker:

```bash
python manage.py test --verbosity 2
```

## CI expectations

Pull requests and pushes to `master` should verify:

- Python 3.11;
- Python 3.12;
- Django system checks;
- migration drift;
- the complete Django test suite;
- Docker Compose configuration;
- Docker image build;
- Django startup/configuration inside the Compose test image.

Avoid duplicating expensive test execution unless it provides distinct coverage.

## Regression policy

Every defect fix should include a test that fails before the fix and passes after it whenever practical.

If a regression test is not practical, explain why in the pull request and identify the alternative validation used.

## Test quality

Tests should be:

- deterministic;
- independent of execution order;
- isolated from external services unless specifically testing an integration boundary;
- clear about the behavior being protected;
- fast enough to run routinely during development.

Use factories/helpers only when repetition becomes significant; avoid adding a test framework dependency merely to remove a few setup lines.
