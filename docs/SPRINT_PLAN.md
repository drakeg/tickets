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

Status: In review. Planned scope: 9 points, TKT-001 through TKT-004.
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
Completion evidence and retrospective are recorded after merge.

## Sprint 7 — Protected ticket lifecycle (proposed)

Goal: agents can triage and resolve tickets without administrator intervention.
Candidate scope: TKT-005/006, 10 points; split if actual capacity is lower.
Entry decision: choose staff-only, assigned-agent, or explicit model-permission
policy for status/assignment changes. Do not infer authorization from public reads.

Acceptance criteria:

- authorized users can close/reopen tickets and update priority/assignment;
- anonymous and unrelated users cannot mutate tickets;
- GET never changes state; POST requires CSRF; invalid targets return 404;
- validation errors retain values and successful actions redirect;
- dashboard totals reflect persisted status changes;
- tests exercise authorized, forbidden, CSRF, invalid-input, and repeat-action paths.

Tasks: refine policy, add protected forms/routes, add UI controls, add request and
dashboard integration tests, update operator docs. Risk: permission mistakes;
mitigation: explicit backend checks and negative tests. Audit history is Sprint 8,
so do not promise historical changes until that increment lands.

## Sprint 8 — Ticket change history (proposed)

Goal: explain ticket changes without inspecting the database.
Candidate scope: TKT-007 (5 points); refine data policy before commitment.
Entry: Sprint 7 merged, author retention and history access policy agreed.
Acceptance: status/assignment changes record actor, timestamp, and old/new values;
failed/forbidden changes create no event; detail history has stable order; existing
tickets migrate safely; no fabricated historical actors/events are backfilled.
Tasks: model/migration, atomic write integration, history UI, authorization and
migration regression tests. Risk: partial writes; validate transactional behavior.

## Sprint 9 — Knowledge reuse (proposed)

Goal: find and maintain solutions that reduce repeated tickets.
Candidate scope: KB-001/002 (8 points), independent of Sprint 8 if reprioritized.
Acceptance: article search handles empty text and paginates; authors/staff can edit
under an explicit policy; other users cannot edit; article author remains stable;
valid edits redirect, invalid forms retain input, missing articles return 404.
Tasks: refine author permissions, shared search/list behavior, edit forms/routes,
request tests, documentation. Risk: unauthorized edits; enforce backend checks.

## Paused Sprint 5 and later refinement

UI-001/002 retain the unfinished frontend work. Return to it as a dedicated
increment after ticket queue delivery or earlier if a security issue requires it.
Do not label Sprint 5 complete while tracked artifacts remain. DATA-001, CMDB-001,
PRJ-001, OPS-001 and API-001 remain ordered candidates, not delivery promises.
