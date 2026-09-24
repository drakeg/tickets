# Coding Standards

These standards apply to application code, tests, infrastructure files, and documentation in this repository.

## Python and Django

- Follow PEP 8 conventions unless existing framework conventions require otherwise.
- Use four spaces for indentation; do not introduce tabs.
- Prefer descriptive names over abbreviations.
- Keep views focused on request/response orchestration. Move reusable business logic into appropriate helpers, services, model methods, or query helpers as complexity grows.
- Prefer explicit Django ORM filters over clever queryset combinations.
- Use `get_object_or_404()` for normal detail-view lookup behavior when a missing object should produce HTTP 404.
- Use `reverse()` / named URLs in tests and application code where practical instead of hard-coded paths.
- Use booleans as booleans rather than string values such as `"True"`.
- Avoid unused imports and dead code.
- Keep environment-specific values out of source code.

## Security

- Never commit credentials or production secrets.
- State-changing actions such as logout, create, update, and delete operations should use appropriate HTTP methods and CSRF protection.
- Apply authentication and authorization explicitly to protected views.
- Do not rely only on UI visibility to enforce permissions.
- Validate and normalize user input before using it in queries or persisted data.
- Keep supported dependencies patched and let CI verify upgrades.

## Django templates

- Use current Django template tags and syntax.
- Keep Bootstrap markup consistent with the Bootstrap version actually loaded.
- Prefer semantic HTML and accessible form controls.
- Avoid duplicate element IDs.
- Use named Django URLs rather than hard-coded internal links.
- Keep JavaScript behavior small and localized; avoid adding new jQuery dependencies when native browser APIs or existing Bootstrap behavior are sufficient.

## Database and migrations

- Every model change that requires a migration must include the migration.
- CI must remain clean under `python manage.py makemigrations --check --dry-run`.
- Avoid destructive schema changes without a documented migration/data plan.
- Add indexes or constraints when a proven query/integrity need exists rather than speculatively.

## Error handling

- Prefer predictable HTTP responses over uncaught exceptions.
- Empty searches and optional filters should return valid empty result sets rather than fail.
- Do not broadly catch `Exception` unless re-raising or handling a clearly documented boundary.
- Log operational failures without leaking secrets.

## Dependencies

- Keep dependencies in `requirements.txt` intentional.
- Review compatibility notes for framework-level upgrades.
- Upgrade one logical dependency group at a time where possible.
- Do not merge dependency updates with unrelated feature work.
- All dependency upgrades must pass the normal test matrix and Docker smoke validation.

## Documentation

Update documentation in the same pull request when changing:

- setup commands;
- environment variables;
- ports;
- Docker behavior;
- CI behavior;
- architecture or developer workflow;
- user-visible behavior that materially changes operation.

## Pull requests

A pull request should:

- have a narrow purpose;
- explain why the change is needed;
- summarize important implementation details;
- identify tests added or run;
- call out migrations, compatibility concerns, or follow-up work;
- avoid unrelated formatting churn.

## Reviews and refactoring

Prefer behavior-preserving refactors with tests already in place. When refactoring untested legacy code, add characterization/regression tests before or alongside the refactor.
