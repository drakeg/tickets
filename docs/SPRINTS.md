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

### Sprint 3 — Authorization and protected writes — Complete

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

Representative pull requests: #157, #158.

### Sprint 4 — Knowledge base core workflows — Complete

Goal: turn the knowledge base from a broken listing into a usable, tested article workflow.

Planned scope:

- repair article listing rendering;
- add public article detail views;
- add authenticated article creation;
- link knowledge-base creation from navigation;
- add regression tests for list, detail, authentication, and creation behavior;
- evaluate search/edit/delete behavior for follow-up work after the core flow is stable.

Acceptance criteria:

- existing articles render correctly in the list;
- article detail pages render by ID and return 404 for missing records;
- anonymous users cannot create articles;
- authenticated users can create articles and are recorded as the author;
- Python 3.11/3.12 tests and Docker Compose validation remain green.

Representative pull requests: #161, #162, #163.

### Sprint 5 — Frontend/runtime hygiene — In progress

Goal: remove legacy development artifacts and reduce outdated frontend/runtime baggage without changing application behavior.

Planned scope:

- remove tracked OS and IDE-generated files;
- keep ignore rules aligned with local development tooling;
- audit legacy frontend libraries and duplicate runtime assets;
- remove obsolete assets only when usage is proven absent;
- preserve existing tested behavior while modernizing incrementally.

Acceptance criteria:

- generated OS/IDE files are no longer tracked;
- repository ignore rules prevent those artifacts from returning;
- frontend/runtime cleanup is backed by the existing functional test suite;
- Python 3.11/3.12 tests and Docker Compose validation remain green.

Representative pull requests: #164, #171, #TBD.

## Future sprint candidates

- deeper Bootstrap/jQuery modernization after usage auditing;
- dependency modernization under the existing CI safety net;
- stronger model validation and data-integrity rules;
- migrating string-based ownership fields to relational user references.
