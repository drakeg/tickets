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

### Sprint 5 — Frontend/runtime hygiene — Paused (carryover tracked)

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

## Runtime support update — September 2026

- Dropped Python 3.11 support to adopt Django 6.1; Python 3.12 is the minimum supported interpreter.
- Updated the CI test matrix and dependency requirement together. Earlier sprint entries document the Python versions tested at that time, not the current support policy.

## Ticket workflow reliability — November 2026 — Complete (#195)

Merged in #195; master Django CI and CodeQL passed. All 51 tests passed.
This focused defect fix interrupted Sprint 5; remaining asset hygiene stays open.

Goal: make ticket submission safe to refresh and the saved ticket useful to read.

Scope and acceptance criteria:

- valid submissions redirect to the newly created ticket;
- refreshing the destination does not create another ticket;
- invalid submissions retain values and errors without saving;
- detail pages show ticket fields, closed/unassigned states, and escaped multiline descriptions;
- missing tickets return 404 and anonymous submissions remain blocked;
- list links use the named detail route;
- restore four missing app package markers so CI discovers every app test module;
- no schema or dependency changes.

Validation: run all six app test modules, Django checks, and migration-drift
checks. Docker Compose verification remains required in CI when Docker is
unavailable locally.

## Future sprint candidates

- deeper Bootstrap/jQuery modernization after usage auditing;
- dependency modernization under the existing CI safety net;
- stronger model validation and data-integrity rules;
- migrating string-based ownership fields to relational user references.

## Sprint 6 — Reachable ticket queues — Complete (#196)

Goal: remove the 15-ticket visibility ceiling and make queue status navigation usable.
Stories TKT-001–004, 9 provisional points. See [detailed plan](SPRINT_PLAN.md)
for acceptance criteria, test approach, risks, and proposed Sprints 7–9;
see [backlog](BACKLOG.md) for ordered carryover and dependencies.

## Sprint 7 — Protected ticket lifecycle — Complete (#197)

Stories TKT-005/006: explicit issues.change_issue permission controls triage
updates (status, priority, assignee). Staff/assignee status alone grants no edit
rights. Tests cover permission boundaries, CSRF, invalid forms, restricted fields,
close/reopen/unassign and dashboard integration. No schema changes.
See [delivery plan](SPRINT_PLAN.md) for review, rollback and follow-up history work.

## Sprint 8 — Ticket change history — Complete (#198)

TKT-007 records transactional triage changes with actor/time and before/after
snapshots. History is permission-gated and paginated. Existing tickets receive no
backfilled events. Includes additive migration 0002 and a preservation rehearsal.
70 tests pass; see the detailed plan for policy, scope boundaries and rollback.

## Navigation and dashboard repair — Complete (#199)

User-reported blocker interrupts planned Sprint 9. Fix nested navigation collapse,
make ticket/project/system/article creation discoverable, replace inert menu links,
and redesign the dashboard with responsive cards and locally served styling.
Create links remain visible when signed out, with a sign-in explanation; backend
login requirements remain enforced. No schema changes. Test navigation, role
visibility, form reachability and local static delivery in Docker.

## Sprint 9 — Knowledge reuse — Complete (#200)

KB-001 completes pagination of existing article browsing/search workflows. KB-002
editing was already present in merged code and is reconciled in the backlog.
Shared rendering orders by date then ID and preserves search text across pages.
Four new regression tests; no migrations. See detailed plan for acceptance and
review scenarios. The live instance remains on merged master pending review.

## Sprint 10 — Project creation feedback — Complete (#201)

PRJ-001: redirect after successful project creation and show complete project
fields with empty-state labels on detail. Invalid forms retain input; anonymous
writes stay protected. Named list links and refresh regression coverage included.
No migration changes. See detailed plan for acceptance, risks and review demo.

## Sprint 11 — Project scheduling input — Complete (#202)

PRJ-002 adds native ISO date widgets and validates the project's end date is not
before its start date. Same-day/partial/blank schedules remain valid. Four new
request-level tests cover invalid ranges, input retention, valid schedules and
calendar-date validation. No schema changes or existing-data edits.

## Sprint 12 — Reachable project lists — Complete (#203)

PRJ-003 paginates browsing, personal/unassigned queues and search, retains encoded
search text and assignment scope, and replaces the inert status switch with real
schedule dates. Five request tests cover reachability, ordering, scope, search,
invalid pages/empty results and list content. No schema changes.

## Accessibility repair — Text contrast — Complete (#204)

User audit reported color-contrast failures. Browser reproduction identified
muted dashboard text and outline buttons against the light workspace background.
Darken shared muted text and outline-button normal/hover/active palettes, without
changing layout or data. Guard the normal-text 4.5:1 threshold with a color-ratio
regression and verify rendered pages with axe-core before/after.

## Accessibility follow-up — Decorative glyph audit — Complete (#205)

The port-8086 workbench reported no confirmed findings after #204, but retained
three incomplete contrast checks for non-text Unicode action icons. Replace those
glyphs with decorative SVGs; preserve visible card labels and existing colors.
Reproduce and verify both findings and incomplete output with the actual scanner.
No schema or dependency changes. Existing audit history is not rewritten.

## Sprint 13 — Inventory creation feedback — Complete (#206)

CMDB-002 redirects successful system creation, expands saved details and explains
missing prerequisite lists. Setup links are gated by staff and model permissions;
backend authentication is preserved. Regression coverage includes creation/refresh,
invalid references, escaped names, missing records and empty-install setup.
No schema changes. See the detailed delivery plan for acceptance and rollback.

## Sprint 14 — Reachable inventory lists — Complete (#207)

CMDB-003 paginates system browsing/search, fixes the blank OS column, uses named
links and joins related values. Five new regressions cover complete reachability,
encoded search, invalid pages/empty results, related fields and bounded queries.
No schema changes. See detailed plan for acceptance criteria and rollback.

## Admin workspace polish — Complete (#208)

UI-004 overrides admin branding and CSS variables to match the main workspace,
including dark mode and responsive layouts. Adds a Back to workspace link and
Priority Meta labels (priorities), with a metadata-only migration. Native admin
components/permissions remain in use; no theme dependency is introduced.
Validate index, list, add form, login restrictions, priority creation, browser
layout and contrast before delivery. Rollback theme files separately from metadata.

## Sprint 15 — Team role foundation — Complete (#209)

P1 RBAC-001 adds Infrastructure Team, Help Desk and Project Manager definitions
and safe setup_roles command. Explicit permission matrix, current limitations,
and backend enforcement stories RBAC-002/003 are tracked in docs/ROLES.md.
Default setup does not elevate or assign users and preserves custom grants.
No schema changes; full application enforcement is the next priority.

Sprint 15 addition: KB-003 provides reviewed ticket-to-article publication with
prefilled issue content, required solution, source link and duplicate protection.
It uses the role foundation's ticket-view/article-add grants. Additive knowledge
migration preserves existing articles; all existing role/access tests remain.

## Sprint 16A — Inventory and search enforcement — Complete (#210)

RBAC-002A protects inventory reads/writes and reference choices, gates inventory
navigation/counts, and replaces unrestricted global search with authorized-model
queries. Explicit group/anonymous/no-role/revocation/multi-role tests are included.
Remaining ticket/project/article direct-route/counter gaps stay next P1 scope.

## Sprint 16B — Ticket role enforcement — Complete (#211)

RBAC-002B protects every ticket read/write route, gates ticket links and counts,
and avoids unauthorized dashboard count queries. Explicit grants replace implicit
public/login-only access. Seven new role-boundary regressions cover direct URLs,
denied writes, partial grants, dashboard disclosures, revocation/union and recovery.
Existing workflow/history/CSRF tests use explicit grants. Project/article policies
remain next P1 scope. No schema changes or automatic membership changes.

## Sprint 16C — Project and knowledge permissions — Complete (#212)

RBAC-002C closes public project/article reads and login-only creation; model grants
now protect direct routes and matching navigation. Project counts and global
search avoid unauthorized model queries. Article edit/delete require their model
grant plus existing author/staff eligibility. Conversion requires destination view
access. Defaults grant no management rights; no schema or membership changes.
Eleven new regressions cover actual role/partial-grant/ownership/CSRF/revocation
boundaries and recovery. Operator verification (RBAC-003) is next P1 scope.

## Sprint 17 — Role and access visibility — Complete (#213)

RBAC-003 replaces the inert profile tabs with truthful account/group/effective
capability details and adds a read-only staff role overview. Requires both staff
status and auth.view_group; edit/user-admin links require their own permissions.
Reports configured group capabilities, missing defaults, extra grants and absent
default groups without changing anything. Eight request regressions cover access,
privacy, partial grants, revocation/union, no writes, escaping and superuser recovery.
No schema, grant, membership or credential changes.

## Sprint 5 carryover — Generated-file repository hygiene — Complete (#214)

UI-001 removes 23 committed artifacts (21 obsolete Python 3.6 bytecode files and two macOS `.DS_Store` files). The existing `.gitignore` already excludes these paths, so no runtime code, settings, migrations, dependencies, or behavior change. Review the deletion-only diff and confirm CI remains green; this does not complete UI-002's frontend dependency audit.

## Sprint 18A — Django admin ticket triage audit — Complete (#215)

TKT-008 first increment extends the existing transactional ticket change history to
individual Django admin edits of status, priority, or assignment. No-op and
content-only saves create no triage events; creation produces no before/after
transition. The actor and historical value snapshots are preserved; an audit
failure rolls back the ticket write. Admin staff restrictions stay enforced.

Review: edit an existing ticket's status/priority/assignee in Django admin and
confirm a single event is visible in the ticket detail to an authorized editor.
Run all tests, Django checks, migration checks and Docker CI. No schema changes.
Follow-up: decide and implement bulk-update audit paths and retention rules
separately, including a policy for destructive deletes before writing code.

 
## Sprint 18B — Audited bulk ticket status actions — Complete (#217)

Add explicit Close selected and Reopen selected Django admin actions, restricted
to authorized change operators. Each changed ticket gets one actor-attributed
before/after event, and unchanged records get no event. Only selected rows are
touched. A transaction rolls back every update when audit writing fails, using
deterministic row locks rather than QuerySet.update().

Acceptance: selection boundaries, no-op/retry safety, close/reopen, actor,
rollback, permission denial, and admin action display. CI must validate Django
tests and Compose smoke checks. No schema or dependency changes. Audit-retention
rules and destructive bulk deletion remain separate policy work.

## Sprint 19A — Standards adoption and LAN setup — Complete (#218)

Goal: apply project-specific Mad Mallard repository standards without touching
active Sprint 18B or any local persisted database. Inspect actual Django/Python,
Bootstrap, SQLite, Compose, GitHub Actions, licensing and release evidence.

Deliver: bounded truthful README badges, AGENTS.md, RELEASES.md, corrected
security policy, maintained CONTRIBUTING guidance, and configurable trusted LAN
hosts. Add CI validation of badge structure and supported documentation.

Acceptance: no invented license/release badges, valid official dynamic CI badges,
no secrets or data deletion, Compose port mapping retained, complete Django CI
and CodeQL successful. Deployment is only verified when an environment is
actually exercised. Sprint 18B remains an independent PR.

## Sprint 19B — SMB pilot readiness — Planned

Goal: shorten the path from local ServDesk to a credible small-MSP pilot.
First, rehearse isolated SQLite backup/restore without touching the user's local
volume, establish a reproducible login/ticket/asset/article smoke test, and
record setup friction. Then obtain real feedback from candidate SMB operators.
An initial two-to-ten-agent pilot and any price are hypotheses, not validation.

## Sprint 19B.1 — SQLite backup safety and restore integrity — Complete (#219)

Add an explicit operator CLI for online SQLite snapshots from the named Compose
volume, no destination overwrite, restrictive snapshot permissions and isolated
restore/integrity verification. Test only synthetic databases in temporary
locations; do not touch the user's persistent volume in CI. Preserve the
full application restore drill and off-device retention policy as follow-ups.

## Sprint 19B.2 — Isolated Django recovery rehearsal — In review

Goal: verify snapshot recovery beyond SQLite integrity checks without accessing
the active database or running destructive migrations against it. The recovery
script copies the supplied snapshot into a temporary directory and checks Django
system configuration, migration compatibility, SQLite foreign keys, and read-only
ORM joins across ticket, asset, knowledge article and project modules.

Two synthetic subprocess tests create migrated data and assert restored ORM
compatibility, plus fail-closed rejection of an unmigrated database. These run in
the Django CI job after dependency installation. No schema changes, environment
changes or production data writes. Application login/UI recovery remains an
explicit next deliverable, not a claimed test result.

## Sprint 19B.3 — SMB demo workflow smoke — In review

Goal: prove ticket-to-knowledge reuse plus inventory and project workflows under
the real named-role permission model. Add synthetic Django request tests for
Help Desk ticket creation, audited triage and linked KB publication; Infrastructure
Team asset creation; Project Manager project creation; and denied cross-role and
anonymous access. Tests run against the framework's isolated test database, not
the persistent Compose volume. Document a repeatable manual demo and future
customer discovery. Do not claim a customer, revenue or willingness-to-pay result.

## Sprint 20A — CMDB system-name validation — Complete (#222)

Require nonblank trimmed names on new system creation and prevent a case-insensitive
name collision within the same cluster. The same name may legitimately exist in
different clusters. Existing systems, including historical duplicate records,
are not rewritten or deleted; the model schema and database are unchanged.

Acceptance: duplicate same-cluster names yield clear inline form errors; case and
leading/trailing whitespace cannot bypass validation; different clusters remain
allowed; invalid references cannot create records; no invalid form causes writes.
Confirm isolated Django regression tests, migration drift, Compose smoke and CodeQL.

Follow-up: inspect historical duplicates and choose safe uniqueness/concurrency
semantics before introducing a database uniqueness constraint, if needed.

## Sprint 20B — Read-only legacy asset name audit — Complete (#223)

Provide an operator command to count blank, whitespace-padded and
case-insensitive same-cluster duplicate system names in existing data without
modification. By default reveal counts only; display record/cluster IDs only
when explicitly requested. Opt-in nonzero exit code supports maintenance
checks without making existing legacy data block ordinary application startup.

Acceptance: empty data, cross-cluster legal duplicates, same-cluster casefold
collisions, whitespace and blank records, privacy-by-default output and
non-destructive behavior. No migrations or production data cleanup. Any future
uniqueness constraint requires a separate data review and explicit migration
policy.

## Sprint 20C — Django admin system-name validation — Complete (#224)

Apply the same blank and same-cluster case-insensitive duplicate checks to
Django admin without removing any existing admin fields. Permit edits that do
not introduce an identity conflict, including existing duplicate names and
blank-name historical rows. No schema changes or automatic cleanup.

Acceptance: admin registration uses the protected form; duplicate/whitespace
and blank new entries are rejected; the same name in another cluster remains
valid; editing legacy duplicates and blank records is possible; renaming a
record into a conflict is denied. Confirm targeted/full Django regression tests,
CodeQL and Docker smoke checks before merging.


## Sprint 21A — Database-enforced unique identifiers for new assets — Complete (#227)

Prevent two concurrently validated web/admin forms from creating equivalent
system identifiers in the same cluster. Add a nullable, database-unique
canonical identity key for newly created assets and records whose actual
cluster/name identity changes. The key combines cluster PK and stripped,
casefolded system name; it remains private to persistence and is not a new
user-editable field. Forms also include legacy whitespace-padded names in
their preflight collision checks.

Safety and migration: the additive column defaults to NULL. Do not backfill
historical records or introduce a restrictive non-null constraint; legacy
duplicate and blank assets remain editable without identity changes. Direct
bulk SQL writes and unmanaged ORM creation paths do not automatically populate
the key; a separate import/ORM contract is needed before promising global
uniqueness. The unique index closes the validation-to-save race **among the
supported form write paths**, not every possible database writer.

Acceptance: sequential new names normalize; independent prevalidated form
instances cannot save a duplicate in the same cluster; admin and application
forms share the key; Unicode casefold/legacy padded collisions are handled;
unchanged old records retain NULL; renaming an old asset assigns its canonical
key; no data loss on migration. Verify makemigrations --check --dry-run, Django
CI, CodeQL, Compose smoke and targeted tests. The race loser may encounter an
integrity error if a simultaneous insert happens after form validation; improve
its user-facing conflict response in a subsequent small increment.


## Sprint 21B — Friendly concurrent identity-conflict responses — Complete (#228)

When another user inserts an asset between form validation and database save,
catch **only** the canonical identity-key unique constraint violation. In the
regular web flow, show the current entered values and a helpful inline field
error, without a 500 or a partially committed asset. In Django admin, return
to the relevant form with a visible error message after its atomic transaction
rolls back; avoid swallowing unrelated database errors.

Acceptance: conflict response and no writes in both paths, unrelated integrity
violations still raise, synthetic tests with injected database conflicts, and
passing full Django/Compose/CodeQL checks. Legacy asset records unchanged.


## Sprint 22A — Search CMDB systems by related fields — Complete (#229)

Improve daily SMB help desk workflows by matching system identifiers and
related vendor, cluster and operating-system names from the same inventory
search field. Preserve stable cluster/name/PK ordering, pagination, escaped
query display and existing view_server access controls. The SQL query joins
existing foreign-key references and does not create duplicate systems for
multi-field matches. No migration, dependency or data changes.

Acceptance: all four search dimensions, case-insensitive partial matches,
duplicate-free results when a system matches multiple dimensions, empty/no
match handling, accessible search label and unchanged unauthorized access
behavior. Confirm full Django/Compose/CodeQL checks and regression coverage.


## Sprint 22B — Search tickets by people and priorities — Complete (#230)

Improve ticket discovery for SMB help desks: extend the existing summary and
description search to requester display name, assigned user name and priority
name. Preserve the existing authorization checks, status filters, stable
newest-first pagination and escaped query display. Improve the accessible
search label and placeholder to explain supported fields.

Acceptance: all five query dimensions, no duplicate rows when multiple
attributes match, status filter preservation, no results for blank input,
permission denial for unauthorized users, safe HTML escaping and passing Django,
Compose, CodeQL and repository-standards checks. No schema or data changes.


## Sprint 22C — Faster repeatable local Docker builds — Complete (#231)

Keep the established Python 3.15-slim base, Compose services, named database
volume and application behavior. Enable Docker BuildKit's pip download cache
for the dependency layer so repeated local image builds can reuse downloaded
packages after manifest updates rather than always downloading every wheel.
A new dependency version still triggers pip resolution and installation.

Acceptance: Dockerfile uses a build-only cached pip directory, no cache
files enter the final image or repository, Compose test image builds and
Django smoke checks pass in CI. No runtime dependency or data changes.
Record that actual wall-clock speedups depend on host cache state and are
not claimed without measurements.


## Sprint 23A — Readable ticket queues — Complete (#232)

Improve daily triage for small support teams by displaying the ticket summary
as a link to its detail, with explicit priority, assigned username (or
Unassigned) and readable Open/Closed status. Remove the misleading non-clickable
checkbox switch and avoid rendering long descriptions in the queue table.
Preserve the existing newest-first pagination, status filtering, search and
permission boundaries. Fetch priority with the existing related-user query to
avoid introducing per-row database lookups.

Acceptance: readable cells for open, closed, assigned and unassigned tickets;
linked summaries; no fake toggle inputs; escaped user-supplied text; unchanged
authorization and filtered search. Verify focused/full Django tests, migration
drift, Compose smoke, CodeQL and standards checks. No migrations or dependency
changes.


## Sprint 23B — Priority filters across ticket queues — Complete (#233)

Help agents focus on high-priority work without manually searching for priority
names. Add a dropdown listing configured priorities alongside the existing
status filter for all, assigned, unassigned, and search queues. Preserve active
query and filter selections across GET submissions and pagination. Reject
invalid or missing priority identifiers gracefully by falling back to all
priorities. The filter does not bypass any existing role or authentication gate.

Acceptance: combined status/priority filtering, queue assignment scoping,
text-search combination, pagination query retention, invalid ID handling,
accessible label and no schema changes. Pass focused/full Django test suite,
Compose smoke, CodeQL and repository standards.


## Sprint 23C — Assignee filters in ticket queues — Complete (#234)

Give authorized ticket readers a dropdown for all assignees, unassigned
tickets, or a specific assigned agent, composable with existing status,
priority and text search filters. Options list only agents with tickets in
the current queue scope, not the entire user directory. Preserve current
assignment boundaries for personal/unassigned queues, safe query parsing,
GET-only filtering, pagination and no-data behavior.

Acceptance: selection by agent and unassigned, combinations with other
filters, search and pagination retention, no other-user choices in scoped
queues, invalid values fallback without exposing tickets, and authorization
checks unchanged. All test coverage and CI/Compose/CodeQL checks must pass;
no schema change or stored-data mutation.


## Sprint 24A — Safe filtered ticket CSV export — Complete (#235)

Let authorized ticket readers download the currently filtered queue as a
streamed CSV without exposing data from other user/assignment scopes.
Reuse the exact status/priority/assignee/text query restrictions used by the
normal list. Include ticket ID, summary, requester, description, priority,
assignee, status and ISO-8601 creation timestamp. Export **all** matching
rows rather than just the visible 15-row page. Protect spreadsheet consumers
against formula injection in user-controlled text cells, use attachment
headers and disable response caching.

Acceptance: normal and filtered CSV rows match queue scope/order; read-only
GET endpoint gated by existing view permission; no unfiltered export bypass;
formula injection prevention including leading whitespace; stable UTF-8
CSV quoting, no full queryset materialization, and empty exports contain a
header. Django CI, Compose, CodeQL and standards must pass. No migration,
dependency or persistent-data changes.


## Sprint 24B — Deterministic ticket queue ordering — Complete (#236)

Make oldest-first work prioritization available beside the default newest-first
ordering for all, personal, unassigned and search queues. Preserve existing
status/priority/assignee/text restrictions, stable pagination using ticket ID
as a tie-breaker, and the currently selected order across search submissions
and CSV downloads. Invalid sort values fall back to newest first.

Acceptance: the same set of tickets is reachable regardless of sort order,
queue/CSV ordering agrees, no authorization change or additional queries per
row, and all Django/Compose, CodeQL and repository checks pass.


## Sprint 25A — Audited quick close/reopen from ticket queues — Complete (#237)

Enable authorized ticket editors to close or reopen requests directly from
queue rows while keeping existing role permissions, CSRF and change history
enforcement. Actions use POST only and reuse the atomic audited bulk status
service for one target issue. No event is created if the requested status is
already current. Invalid actions, nonexistent ticket IDs, anonymous users and
read-only users cannot mutate status. Return to ticket detail for confirmation
after a successful change.

Acceptance: close/reopen buttons appear only to users with change_issue;
POST-only and CSRF-protected, authenticated plus explicit ticket view/change
permissions, history captures actor/snapshot, repeated requests are idempotent,
no privilege bypass and no migrations/dependencies. Full Django/Compose,
CodeQL and repository standards checks required.


## Sprint 25B — Permission-scoped audit history CSV — Complete (#238)

Give authorized ticket editors an audit trail they can retain for external
review without exposing history to read-only or anonymous users. Export a
single ticket's change history with actor, timestamp and before/after status,
priority and assignee values. Use a streamed CSV, stable newest-first order,
formula-safe values, and private/no-store headers. The link appears alongside
the existing permission-gated change history display, and this is read-only.

Acceptance: actor and before/after fidelity, no cross-ticket history leakage,
CSVs escaped against spreadsheet formula injection, view+change permission
required, read-only users see no export link, missing tickets return 404,
no data/migration changes, full CI and local tests pass. Retention/deletion
policy remains an explicit separate decision.


## Sprint 26A — Atomic ticket claim to self — Complete (#239)

Let an authorized support agent claim an open, unassigned ticket from the
queue using a CSRF-protected POST action. Reuse row locking and actor-attributed
IssueChange history. Closed or already assigned tickets cannot be claimed;
a failed claim returns an explicit HTTP 409 conflict instead of silently
reassigning the existing owner. Read-only users cannot see or invoke the action.

Acceptance: ownership and audited before/after snapshots, deterministic
no-op/conflict handling on repeated or competing claims, role boundary,
CSRF protection, GET rejection, missing-ID handling, and no schema changes.
Confirm targeted/full Django tests, Docker smoke, CodeQL and standards.


## Sprint 26B — Owner-only ticket release — Complete (#240)

Allow an authorized agent to return their own **open** ticket to the unassigned
pool via a protected POST action. The existing assigned user must match the
actor; a team member cannot release another person's ticket even if they
have broad ticket change permission. A concurrent or repeated release returns
HTTP 409 with no write. The ownership transition is recorded with one
IssueChange before/after snapshot, preserving ticket status and priority.

Acceptance: owner release works; nonowners/read-only/anonymous/GET and
closed-ticket cases cannot change ownership; repeated requests are non-writing,
CSRF is enforced and queue controls show only where appropriate. Full Django
CI, Compose, CodeQL and standards validation. No migration or data loss.


## Sprint 26C — Detail-page ticket ownership controls — Complete (#241)

Expose the existing Claim and Release actions beside the ticket description,
not only from queue rows. The detail view must show Claim only when the ticket
is open and unassigned; show Release only when the current editor is its owner;
and hide both for read-only users, other agents and closed tickets. Buttons
submit to the existing CSRF-protected, audited endpoints. No duplicate update
logic, schema change, or additional permissions.

Acceptance: permission-aware control visibility and actual audited transitions,
with view tests and all CI/Compose/CodeQL checks green.


## Sprint 27A — Aging open-ticket triage — In review

Let agents locate tickets that have remained open for longer than 24 hours,
3 days or 7 days. The age is measured from the existing ticket creation time,
not last updated time or an SLA deadline. Apply the selected threshold to open
tickets only; closed tickets are excluded even if the status filter says all.
Combine with current query, assignee, priority and sort controls, and preserve
the filter in pagination and CSV exports. Reject other age inputs safely.

Acceptance: timezone-aware cutoff checks, threshold behavior, combined filters,
CSV parity, empty results, invalid inputs and permission boundaries tested.
No migration, data changes, or invented service-level commitments. Full Django
CI/Compose, CodeQL and repo standards checks required before merging.
