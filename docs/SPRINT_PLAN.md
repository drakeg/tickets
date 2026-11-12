# Delivery plan

Updated: 2026-11-12. Source of scope: [product backlog](BACKLOG.md).
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

## Sprint 9 — Knowledge reuse — In review

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
