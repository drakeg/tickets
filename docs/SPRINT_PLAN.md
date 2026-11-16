# Delivery plan

Updated: 2026-11-14. Source of scope: [product backlog](BACKLOG.md).
Historical evidence: [sprint history](SPRINTS.md).

## Working agreement

Use one active delivery sprint at a time. Sprint 5 is paused with explicit
carryover; Sprint 6 prioritizes a ticket navigation defect. Use a nominal one-week
planning window, adjusted to available capacity; this is not a dated commitment.
Greg is the product decision maker and merge reviewer. Implementation and test
work proceeds in reviewable PRs; merging or deployment is not automatic.

At planning, confirm the goal and ready stories. During work, record progress,
blockers, scope changes, and test evidence below. At review, demonstrate the
acceptance scenarios and link CI. After merge, record a short retrospective:
what worked, what failed, and one concrete next improvement. Do not mark the
sprint complete until master CI is green and remaining work is accounted for.

## Sprint 6 — Reachable ticket queues

Status: Complete (#196). Delivered scope: 9 points, TKT-001 through TKT-004.
Goal: every existing ticket remains reachable as ticket volume grows.

### Stories and acceptance criteria

| Story | Acceptance criteria | Verification |
|---|---|---|
| TKT-001 (3) | All, assigned, unassigned, and search lists paginate at 15; order is date descending then ID descending; no ticket is lost at page boundaries; invalid pages recover safely | Multi-page fixtures with equal timestamps; uniqueness and ordering checks; malformed/out-of-range page checks |
| TKT-002 (3) | All/open/closed filters combine with queue ownership and search; unknown status falls back to all; pagination retains encoded search text and status; empty results render normally | Status counts; assignment boundaries; special-character search; empty search |
| TKT-003 (1) | Issues navigation links to all and closed queues; closed link replaces the inert Complete link | Rendered route assertions and request checks |
| TKT-004 (2) | Versioned backlog has priorities, points, dependencies, states; sprints have goals, acceptance criteria, risks, and evidence; current runtime docs agree with CI | Documentation review against workflows and implemented behavior |

### Tasks and review evidence

- Implement shared queue rendering, filtering, related-user loading, and pagination.
- Add accessible labeled filter controls and previous/next navigation.
- Add regression coverage before considering stories done.
- Run full default suite, system checks, migration-drift and whitespace checks.
- Existing CI verifies Python 3.12, Docker Compose smoke, and CodeQL.
- No schema changes. Public read access and authenticated personal queues keep
  their existing authorization behavior.

Risk: changing the main list from oldest-first to newest-first is intentional.
Tie-breaking by ID prevents overlap for equal timestamps; concurrent insertion
can still shift offset pages. Cursor pagination is deferred until warranted.
Rollback: revert the PR; there is no data migration to reverse.

Review demo: create more than 15 tickets, inspect page 2, filter closed tickets,
search with an ampersand, and visit Assigned to me as two different users.
Completion evidence: #196 merged; all 57 tests passed locally and master CI
passed Django/Compose and CodeQL. Retrospective: shared queue rendering kept
filter behavior consistent; offset paging remains sensitive to concurrent inserts.
Next improvement: protect lifecycle writes with explicit model permissions.

## Sprint 7 — Protected ticket lifecycle — Complete (#197)

Goal: agents can triage and resolve tickets without administrator intervention.
Committed scope: TKT-005/006, 10 provisional points.
Policy: explicit Django `issues.change_issue` permission (including superusers).
This follows Django's existing Issue model permission rather than introducing a
new role. Staff status and being the assignee alone do not grant access. Permission
is global across tickets and can be delegated through Django admin users/groups.

Acceptance criteria:

- authorized users can close/reopen tickets and update priority/assignment;
- anonymous and unrelated users cannot mutate tickets;
- GET never changes state; POST requires CSRF; invalid targets return 404;
- validation errors retain values and successful actions redirect;
- dashboard totals reflect persisted status changes;
- tests exercise authorized, forbidden, CSRF, invalid-input, and repeat-action paths.

Tasks: refine policy, add protected forms/routes, add UI controls, add request and
dashboard integration tests, update operator docs. Risk: permission mistakes;
mitigation: explicit backend checks and negative tests. Implementation evidence: restricted triage ModelForm, GET/POST edit route,
permission-gated detail link, POST redirect, explicit update_fields to preserve
content/requestor/date. Regression coverage includes close/reopen/unassign,
repeat writes, invalid choices, missing records, method restrictions, actual CSRF
checks, UI visibility, unauthorized staff/assignee denial, and dashboard totals.
No migrations. Review demo: grant change permission to a non-staff user; update a
ticket, close/reopen it, then revoke permission and verify writes are forbidden.
Rollback: revert the PR; already saved ticket values remain persisted.
Audit history is Sprint 8,
so do not promise historical changes until that increment lands.

Sprint 7 completion: #197 merged; master Django CI/Compose and CodeQL passed.
All 64 local tests passed. Retrospective: model permissions enabled delegated
triage without staff privileges. Next improvement: transactional history writes.

## Sprint 8 — Ticket change history — Complete (#198)

Goal: explain ticket changes without inspecting the database.
Committed scope: TKT-007 (5 points). Sprint 7 is merged.
Policy: history is visible only with issues.change_issue, consistent with triage
access. Actors use nullable SET_NULL references plus stored username snapshots;
priority/assignee snapshots retain IDs and names. Deleting tickets cascades history.
No fabricated events are backfilled. Only changes through the triage form are
recorded; admin and bulk writes are tracked as TKT-008 follow-up work.
Acceptance: status/assignment changes record actor, timestamp, and old/new values;
failed/forbidden changes create no event; detail history has stable order; existing
tickets migrate safely; no fabricated historical actors/events are backfilled.
Tasks: model/migration, atomic write integration, history UI, authorization and
migration regression tests. Risk: partial writes; ticket and event creation use one atomic transaction.
The service re-reads the ticket under select_for_update before computing snapshots.
SQLite has no row locks; stronger concurrent-write guarantees require a backend
with row locking. History is paginated at 10 entries, ordered by timestamp then ID
descending. No-op, invalid, forbidden and GET requests create no history.

Evidence: all 70 tests pass, system checks and migration drift pass. Six new tests
cover snapshots/no-ops, rejected requests, rollback on history failure, deleted and
renamed actors, permission-gated escaped rendering, and stable scoped pagination.
An isolated SQLite migration rehearsal seeded an existing closed ticket at 0001,
applied current migrations, and verified preserved fields and zero invented events.
Docker is unavailable locally; existing CI verifies the Compose image.

Review demo: change priority/assignee/status, inspect recorded before/after values,
repeat the same save, and verify history is hidden without edit permission.
Rollback: reverting code can leave the added table in place; reversing issues 0002
drops recorded history and requires an explicit backup/retention decision.

## Sprint 9 — Knowledge reuse — Complete (#200)

Goal: all knowledge articles remain reachable as the collection grows.
Committed increment: KB-001 (3 points). Inspection of merged master found search
and author/staff edit/delete workflows already implemented, so KB-002 is recorded
as existing functionality rather than recreated. Existing authorization tests stay
in the suite; broader author-identity migration remains DATA-001 follow-up work.

Acceptance criteria:

- article browsing and searches paginate at 15 without dropping older records;
- date descending then ID descending gives stable ordering for equal timestamps;
- previous/next links preserve the trimmed, URL-encoded search phrase;
- empty queries and no-match searches remain valid empty results;
- malformed page values fall back safely; out-of-range pages select the last page;
- existing create/edit/delete authorization and redirect tests continue passing.

Tasks: share list rendering, add page navigation, add multi-page request tests,
reconcile the backlog with current code, and run full tests/checks. No migration
or dependency changes. Risk: offset pages may shift during concurrent article
creation; cursor pagination is deferred. Rollback: revert this increment.

Review demo: seed more than 15 articles in an isolated test database, browse every
page, search a phrase containing an ampersand, and verify no unrelated results.
Keep the user's live Docker instance on merged master while this PR is reviewed.
Evidence: four pagination regressions cover stable reachability, encoded search,
invalid page fallback and empty results; full-suite results recorded in the PR.

## Paused Sprint 5 and later refinement

UI-001/002 retain the unfinished frontend work. Return to it as a dedicated
increment after ticket queue delivery or earlier if a security issue requires it.
Do not label Sprint 5 complete while tracked artifacts remain. DATA-001, CMDB-001,
PRJ-001, OPS-001 and API-001 remain ordered candidates, not delivery promises.

## Urgent navigation repair — Complete (#199)

UI-003 interrupts Sprint 9 after local user feedback. Goal: navigation and record
creation must be discoverable without dropdown JavaScript, on wide and narrow
screens. Replace nested collapsed wrappers with direct responsive sidebar links;
show explicit login guidance; keep backend authentication and staff checks intact.
Dashboard uses linked count cards and four create actions. Bootstrap CSS is
vendored with its license; no external styling request is needed. Legacy account
section switching uses a small native script. Existing date forms remain Django
form controls; the old datepicker enhancement is removed with the shared jQuery
runtime. Invalid date input continues to use existing server-side validation.

Acceptance: direct links reach all four create forms after login; anonymous users
are redirected to login by each create endpoint; admin links remain staff-only;
sidebar and create cards remain available without JavaScript; existing issue,
project, inventory, knowledge and account tests pass. Review at desktop and mobile
widths. No migration. Roll back by reverting this UI-only PR.

Navigation repair completion: #199 merged; master Django CI and CodeQL passed.
Local Docker instance updated to merged master, health and HTTP checks passed.

## Sprint 10 — Project creation feedback — Complete (#201)

Goal: a successful project submission leads to a useful saved record, and
refreshing that page does not create another project. Scope: PRJ-001 (3 points).
Entry: Sprint 9 merged with passing master CI; local Docker follows merged master.

Acceptance criteria:

- valid authenticated creation redirects to the new project's named detail route;
- refreshing the destination leaves exactly one project;
- requestor comes from the signed-in user and creation date is server-generated;
- invalid submissions retain entered values/errors without creating a record;
- detail shows summary, description, requestor, assignee and dates;
- optional assignee/dates show Unassigned/Not scheduled rather than blank output;
- descriptions are escaped and retain line breaks; missing projects return 404;
- anonymous POST remains blocked and list links use named routes.

Tasks: apply post/redirect/get, expand detail template, replace hardcoded list
links, add regression tests, update user docs. No migration/dependency changes.
Evidence: full-suite/check results appear in the PR. Review demo: create a project,
refresh its detail page, and inspect an unassigned project without dates.
Risk: the detail page exposes the same fields already public in project lists;
read permissions remain unchanged. Rollback: revert PR without data migration.
Deferred: project pagination, lifecycle state and scheduling validation remain
separate refinement items rather than being mixed into creation feedback.

Sprint 9 retrospective: reused existing search/edit flows rather than duplicating
them; four new pagination cases brought the suite to 76 passing tests. Follow-up:
review the next domain's create/detail workflow with the same regression pattern.

## Sprint 11 — Project scheduling input — Complete (#202)

Goal: make project dates easy to enter and reject reversed date ranges at project
creation. Scope: PRJ-002 (3 points), refining the scheduling follow-up from Sprint
10. No new role policy, database migration or dependency is needed.

Acceptance criteria:

- start and end dates use native HTML date controls without a CDN or JavaScript;
- an end date before the start date returns a field error and saves no project;
- rejected input retains the submitted dates and description for correction;
- same-day and forward schedules save and redirect normally;
- both blank dates and either date alone remain valid;
- impossible calendar dates are rejected by the server, independently of browser checks;
- existing authentication, creation and detail regressions remain passing.

Tasks: configure ISO-valued date widgets, add form-level date comparison, exercise
real request submissions, and document behavior. Validation covers full-suite,
Django checks, migration drift and Docker CI. Review demo: submit a reversed range,
correct the end date, then create a same-day and unscheduled project.

Risk and scope: validation applies to the application creation form, not direct
ORM/admin writes; existing stored schedules are not modified. Database-wide
constraints/data cleanup require separate refinement. Native picker presentation
varies by browser, with server validation as the shared boundary. Rollback: revert
this form-only increment; saved project data remains unchanged.

Sprint 10 retrospective: #201 merged; 81 tests passed and master CI verified.
The creation redirect/detail pattern is now shared by tickets and projects.
Follow-up: improve schedule entry without expanding into project lifecycle work.

## Sprint 12 — Reachable project lists — In review

Goal: all projects and search results remain reachable as volume grows, with
accurate list fields. Scope: PRJ-003 (3 provisional points). Entry: #202 merged,
master Django CI and CodeQL green. No schema/dependency changes.

Acceptance criteria:

- all/my/unassigned/search lists paginate at 15, newest first with ID tie-breaking;
- moving between pages retains the current route's assignment restrictions;
- search links preserve the trimmed URL-encoded phrase and exclude nonmatches;
- invalid page input falls back safely; empty results render without page links;
- list shows summary, assignment and actual schedule dates, replacing the disabled
  Closed/Opened switch because Project has no corresponding lifecycle state;
- missing assignment/dates display explicit labels; a direct create action is visible;
- existing authorization, date validation and creation/detail tests still pass.

Tasks: share query rendering/pagination, load related assignees with the page,
update list columns and accessible search/page controls, add multi-page fixtures,
run full suite/checks and verify Docker CI. Review demo: browse more than 15
projects, follow My projects/Unassigned, and search a phrase with an ampersand.
Risk: main list intentionally changes from oldest-first to newest-first; offset
pages can shift under concurrent inserts. Cursor pagination remains deferred.
Rollback: revert the PR; no migration or saved-data changes.

Sprint 11 retrospective: #202 delivered native date controls and server-side
schedule validation, with 85 passing tests and green master CI. Project list
reachability is the next bounded increment. Live Docker remains on merged code
with its LAN binding and allowed hosts preserved while this PR is reviewed.

## Sprint 13 — Inventory creation feedback — Complete (#206)

Goal: make system creation usable on both an empty installation and a configured
inventory. Scope: CMDB-002 (3 points). Entry: #205 merged; master CI verified green.
CMDB-001 identifier normalization/data constraints remain separate discovery work.

Acceptance criteria:

- valid authenticated creation redirects to the saved system's named detail route;
- refreshing the destination does not resubmit the creation form;
- details show name, operating system, vendor, cluster and creation date;
- missing reference choices identify exactly which lists need administrator setup;
- staff with the relevant add permissions receive working Django admin setup links;
- non-staff users receive guidance without administration links;
- invalid reference values retain input/errors without saving; anonymous POST stays blocked;
- missing records return 404 and rendered system names remain escaped.

Tasks: apply post/redirect/get, expand system details, detect empty form querysets,
add permission-gated setup links and request tests, and update user instructions.
Review demo: start with no reference records, add prerequisites as administrator,
submit a system, then refresh the detail page. No schema/dependency changes.
Risks: setup uses existing Django admin permissions; this does not grant new
administration rights. Read permissions and required foreign keys remain unchanged.
Rollback: revert the PR; no migration or persisted-data changes are necessary.
Validation: full suite, system checks, migration drift, diff checks and Docker CI.
The live LAN instance remains on merged code until this increment is reviewed.

Accessibility retrospective: #204 fixed confirmed contrast failures; #205 resolved
three incomplete glyph checks. The actual workbench scan returned both empty
findings and incomplete arrays. Preserve those fixes while developing inventory.

## Sprint 14 — Reachable inventory lists — In review

Goal: every system stays reachable, with correct related data and bounded query
cost. Scope: CMDB-003 (3 points). Entry: #206 merged; master CI green; local Docker
updated and verified healthy on the existing LAN binding.

Acceptance criteria:

- system browsing and name search paginate at 15 and expose all matching records;
- order is cluster ID, system name, then record ID, maintaining cluster grouping
  while making equal-name boundaries deterministic;
- search paging preserves the trimmed, encoded phrase and excludes nonmatches;
- malformed/out-of-range pages recover safely and empty results show no page links;
- operating-system values render from the actual os relationship;
- detail links use named routes and Add system is directly discoverable;
- cluster/vendor/OS columns are selected with the page rather than queried per row;
- existing creation/setup and authorization coverage remains passing.

Tasks: shared list renderer, pagination UI, correct OS binding, related-object
loading, request and query-count regressions, user docs. Review demo: browse 35
systems spread across two clusters, search with an ampersand, inspect OS values
and follow a detail link. No schema/dependency changes or data edits.
Risk: alphabetical ordering within a cluster replaces previously unspecified
row order. Offset pages may shift during concurrent inserts. Rollback: revert PR.
Performance evidence: an anonymous rendered 15-row page performs only the count
and joined page queries. Keep this assertion scoped to the public list request.
Local deployment remains on merged master until this increment is reviewed.

Sprint 13 retrospective: the 98-test suite and master CI passed; missing reference
data now has actionable setup guidance. Next, finish list reachability without
mixing in speculative identifier constraints or cleanup of existing records.

## Sprint 15 — Team role foundation — Complete (#209)

Goal: make the three requested team roles provisionable, with an explicit access
matrix and honest enforcement boundaries. Scope: RBAC-001 (3 points). Role access
is now the next P1 epic; broader feature work yields to RBAC-002 and RBAC-003.

See [role matrix and delivery sequence](ROLES.md) for default grants, setup,
assignment, current route gaps and the Sprint 16 enforcement plan.

Acceptance: Infrastructure Team, Help Desk and Project Manager groups can be
created repeatedly; default grants contain no delete/user/group-management rights;
custom grants/memberships remain; no user is elevated or assigned automatically;
dry-run writes nothing; missing permissions fail before any groups are created;
existing ticket triage recognizes group grants without staff status.

Tasks: define defaults, add transactional setup command, add request/command
regressions, document exact limits and prioritize full enforcement next. No schema
migration. Review demo: preview setup, create roles, assign a test user deliberately,
verify ticket permission and admin denial. Rollback: leave the groups untouched
until administrators decide membership/grant changes; reverting the command does
not remove permissions from users. Foundation is not full RBAC and must not be
presented as such. Full suite, checks and Docker CI remain required.

### Sprint 15 scope addition — KB-003: Ticket-to-article workflow (5 points)

User-requested addition alongside the role foundation; delivered in the same PR
to avoid conflicting role/backlog changes. On saved ticket details and triage form,
users with view_issue plus add_article can open a prefilled knowledge form. Summary
becomes title, full description becomes Issue / symptoms, and summary seeds editable
keywords. Technician adds a required tested solution and reviews before publishing.

Acceptance: GET creates no record; sensitive details can be removed before sharing;
full problem/solution text is not truncated; author/time are server-controlled;
POST/CSRF and both permissions are enforced; repeated saves reuse one source-linked
article without overwriting it; source ticket is not changed or closed; ticket
links to published knowledge; solution/problem are searchable and escaped; deleting
the source ticket preserves knowledge. No automatic publication of copied data.

Migration adds blank problem/solution fields and nullable unique source_issue;
existing articles retain their existing title/keywords/author/date, with blank
new content and no source. A migration rehearsal verifies this path. Generic
article creation/editing also exposes the new body fields; existing articles do
not require a retroactive solution. Conversion requires a solution explicitly.

Review demo: Help Desk member opens a ticket, selects Create knowledge article,
checks copied fields, adds solution, publishes, then follows View knowledge article.
Save pending ticket edits before leaving triage. Knowledge remains public under the
current read policy; RBAC-002 will address that gap. Rollback: keep added fields
when reverting code; reversing the migration removes saved solution/source data
and requires a backup/retention decision. Eight new request regressions cover the
workflow; all existing role tests remain required.

## Sprint 16A — Inventory and search enforcement — Complete (#210)

Goal: enforce the first module's team boundaries without leaving a global-search
back door. RBAC-002A (5 points) is the first split of the P1 RBAC-002 epic.
See docs/ROLES.md for current versus remaining enforcement and exact grants.

Acceptance: anonymous inventory requests redirect; authenticated users without
permissions get 403; Infrastructure can create, Help Desk can read, Project Manager
cannot view inventory by default; staff alone grants no inventory rights; creation
reference choices require their view grants. Hide inventory counts/navigation from
denied users. Global search requires login and filters each model by view grants.
Revocation and multi-role union must take effect on the next request. Preserve
superuser recovery, existing CSRF and data-validation tests.

Tasks: backend decorators, permission-sensitive inventory UI/dashboard, replace
unrestricted Watson route with bounded authorized-model search while retaining its
named URL, denial page, and real group/URL/search tests. No schema changes.
The list still uses two inventory queries; request authentication adds its own
bounded queries, which are excluded from the domain-query regression count.

Review: Infrastructure non-staff user adds system/vendor without entering admin;
Help Desk reads but cannot POST a system; Project Manager sees no system count or
search result. No-role user cannot bypass direct URLs. Role setup assigns nobody.
Risk: existing non-superuser accounts without grants lose inventory access by
design. Assign groups explicitly via admin; do not auto-grant staff accounts.
Rollback: revert route/UI enforcement (reopens previous access), retaining groups.
Next: ticket/project/article routes and their counters, then broader role audit.

## Sprint 16B — Ticket role enforcement — Complete (#211)

Goal: complete RBAC-002B (5 points), making ticket entry points enforce the team
matrix. Reads require view_issue; creation additionally requires add_issue and
view_priority; triage additionally requires change_issue and view_priority. The
priority grant permits reference choices; assignee selection retains existing
site-wide behavior. Grants remain global rather than per-ticket ownership.

Acceptance: anonymous redirects, authenticated 403 before record lookup/form
construction, no denied POST mutation/history, no staff/assignee bypass, role union
and revocation effective next request, superuser recovery, hidden ticket links and
no ticket count query for unauthorized dashboards. Preserve pagination, validation,
transactional audit and CSRF. Full suite and CI must pass.

Tasks: backend decorators, matching navigation/dashboard gates, authorized fixtures,
seven real role regressions and current policy documentation. No migration or new
dependency. Review: Help Desk creates/triages, Infrastructure triages but cannot
create, Project Manager reads only. Admin assignment is deliberate; existing users
without grants lose access by design. Rollback reverts guards/UI but reopens prior
access; keep groups and data. Next sprint addresses project/article route policies.

## Sprint 16C — Project and knowledge permissions — In review

Goal: RBAC-002C (5 points) closes the remaining project/article route gaps in the
module enforcement epic. Project reads/queues/search require view_project;
creation also requires add_project. Knowledge reads/search require view_article;
creation also requires add_article; edit/delete additionally require their model
grant AND existing author/staff eligibility. Superusers retain recovery access.
Ticket conversion requires view_issue, view_article and add_article. Model grants
remain site-wide; project tasks have no separate application workflow yet.

Acceptance: all anonymous direct requests redirect; logged-in denials return 403
before record lookup/form construction; no denied writes; no project count query
or denied model search query; each role can read both domains, only Project Manager
creates projects, each role can publish articles, none receives edit/delete grants.
Partial write-only grants cannot bypass destination view requirements. Authorship
and staff status alone grant nothing; management permissions do not bypass the
existing owner/staff rule. Next-request revocation/combined roles, CSRF, method
restrictions and superuser recovery must pass request tests.

Tasks: route guards, matching shared/domain navigation and dashboard controls,
article controls for each independent grant, role-assignment guidance for accounts
without access, explicit behavioral fixtures and 11 new boundary regressions.
Run full tests, Django checks, migration drift check, Docker suite/smoke and CI.
No dependencies, migrations, group grant changes or automatic memberships.

Review: Help Desk reads projects but cannot create; Project Manager creates; all
three publish knowledge. An article author must receive change_article explicitly
to edit, or delete_article to delete. An administrator reviewing others' articles
needs staff status plus those grants. Existing accounts without grants need a
role assigned deliberately in admin. Rollback reverts route/UI guards (reopening
prior access); retain groups and content. Next: RBAC-003 operator verification and
review of author identity strings/record-level scope as separate policy work.
