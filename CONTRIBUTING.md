# Contributing

This project uses small, reviewable pull requests, automated tests, and sprint-based delivery.

## Development workflow

1. Start from the latest `master`.
2. Create a focused branch for one coherent change.
3. Add or update tests with every behavior change.
4. Update documentation when commands, configuration, APIs, workflows, or user-visible behavior change.
5. Run the relevant local tests before opening a pull request.
6. Open a pull request with a concise summary, test evidence, and any migration or compatibility notes.
7. Merge only after required CI checks are green.

Prefer small pull requests that are easy to reason about and revert. Do not combine unrelated refactors, dependency upgrades, and feature changes unless they are required for the same outcome.

## Branch naming

Use a short category prefix:

- `feature/<name>`
- `fix/<name>`
- `test/<name>`
- `docs/<name>`
- `chore/<name>`
- `security/<name>`

## Definition of done

A change is complete when:

- the requested behavior works;
- relevant tests exist and pass;
- Django system checks pass;
- migration drift checks pass;
- Docker Compose remains usable for local validation;
- documentation is current;
- no known regression is intentionally left behind without an issue or documented follow-up;
- CI is green.

## Project documentation

- [Sprint process and history](docs/SPRINTS.md)
- [Coding standards](docs/CODING_STANDARDS.md)
- [Testing standards](docs/TESTING.md)

## Security

Do not commit passwords, API keys, production secret keys, personal access tokens, or other credentials. See [SECURITY.md](SECURITY.md) for vulnerability reporting guidance.
