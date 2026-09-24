# Sprint Process and History

## Sprint model

Development is organized into short, outcome-focused sprints. A sprint groups related work around a clear engineering objective rather than an arbitrary number of commits.

Each sprint should have:

- a goal;
- a small set of scoped work items;
- acceptance criteria;
- tests and documentation requirements;
- a recorded completion state.

When a sprint is complete and the repository is healthy, development may proceed directly to the next planned sprint without requiring a separate completion confirmation.

## Sprint planning rules

A sprint should:

- solve one coherent problem area;
- prefer several small pull requests over one large pull request;
- keep `master` releasable;
- include regression tests for defects fixed;
- keep local Docker Compose instructions and CI aligned;
- update this document when the sprint scope or status changes.

Urgent security or build fixes may interrupt a sprint. Record them in the sprint history when they materially affect the project.

## Definition of sprint complete

A sprint is complete when:

- all planned work is merged or explicitly deferred;
- required CI is green on `master`;
- local development remains reproducible;
- tests cover the important behavior introduced or fixed;
- documentation reflects the current system;
- unresolved follow-up work is captured for a future sprint.

## Sprint history

### Sprint 0 — Stabilization and CI foundation — Complete

Goal: establish a trustworthy baseline for modernizing the legacy Django application.

Completed work included:

- added Django CI on Python 3.11 and 3.12;
- removed obsolete/incompatible Django integrations;
- constrained Django to supported major versions;
- removed unused GIS/GDAL configuration;
- moved security-sensitive runtime settings to environment variables;
- removed repository-documented default administrator credentials;
- modernized the shared Django/Bootstrap template path;
- removed the duplicate legacy CodeQL workflow.

Representative pull requests: #145, #146, #149, #150.

### Sprint 1 — Local development and functional testing — Complete

Goal: make the application easy to run and verify locally and expand meaningful automated coverage.

Completed work included:

- added `Dockerfile` and `docker-compose.yml`;
- added a persistent local SQLite volume;
- added a dedicated Compose test service;
- added Compose validation/build/smoke checks to CI;
- added functional tests for issues, projects, inventory, and knowledge base behavior;
- fixed project detail/search defects;
- fixed empty search failures;
- fixed inventory operating-system routing.

Representative pull request: #151.

### Sprint 2 — Authentication and dashboard reliability — Complete

Goal: protect core account flows and verify dashboard aggregates.

Completed work included:

- required authentication for profile access;
- corrected registration form handling;
- switched logout to a CSRF-protected POST flow;
- added registration/login/logout/profile tests;
- added data-driven dashboard metric tests;
- fixed the dashboard's undefined ticket progress maximum;
- simplified dashboard issue-count queries.

Representative pull requests: #152, #153.

### Sprint 3 — Authorization and protected writes — In progress

Goal: enforce backend authorization for state-changing and user-scoped application workflows.

Planned scope:

- require authentication for issue, project, and inventory creation;
- require authentication for current-user assignment views;
- restrict vendor administration to staff users;
- add regression tests for anonymous, authenticated, and staff authorization boundaries;
- keep UI behavior aligned with backend permissions in follow-up work if needed.

Acceptance criteria:

- anonymous users cannot create issues, projects, servers, or vendors;
- anonymous users cannot access "my issues" or "my projects" views;
- non-staff users cannot create vendors;
- staff users retain vendor administration access;
- Python 3.11/3.12 tests and Docker Compose smoke validation remain green.

Representative pull requests: #TBD.

## Future sprint candidates

- replacing remaining legacy Bootstrap/jQuery-era markup and dependencies;
- completing knowledge-base CRUD behavior;
- dependency modernization under the existing CI safety net;
- cleanup of tracked editor/OS artifacts and obsolete project files;
- stronger model validation and data-integrity rules.
