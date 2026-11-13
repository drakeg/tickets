# Product backlog

Updated: 2026-11-13. Product: ServDesk (`drakeg/tickets`).

## Product goal

Give a small support team one reliable place to triage tickets, track projects
and assets, and publish reusable solutions. Deliver ticket handling first, then
improve adjacent workflows under the same authentication and quality standards.

## Prioritization and estimates

P1 = next delivery, P2 = subsequent release, P3 = exploratory. Points are relative
complexity estimates (1, 2, 3, 5, 8), not elapsed days. Split items larger than 8.
Order within a priority reflects value, risk, and dependencies. Estimates are
provisional until refinement; no measured velocity or delivery dates are assumed.

| ID | Priority | User story / outcome | Points | Sprint | State | Dependency |
|---|---|---|---:|---|---|---|
| UI-003 | P1 | As a user, navigate and find create actions on desktop/mobile with readable dashboard styling | 5 | Urgent repair | Done (#199) | User-reported blocker |
| TKT-001 | P1 | As an agent, reach every ticket in stable newest-first pages | 3 | 6 | Done (#196) | #195 merged |
| TKT-002 | P1 | As an agent, filter all, assigned, unassigned, and search queues by status | 3 | 6 | Done (#196) | TKT-001 |
| TKT-003 | P1 | As an agent, open closed tickets from navigation | 1 | 6 | Done (#196) | TKT-002 |
| TKT-004 | P1 | As a maintainer, find priorities, acceptance criteria, and sprint evidence in the repo | 2 | 6 | Done (#196) | None |
| TKT-005 | P1 | As an authorized agent, close/reopen a ticket using protected POST actions | 5 | 7 | Done (#197) | Explicit issues.change_issue permission |
| TKT-006 | P1 | As an authorized agent, change assignment and priority | 5 | 7 | Done (#197) | TKT-005 permission policy |
| TKT-007 | P2 | As a reviewer, see who changed status/assignment and when | 5 | 8 | Done (#198) | TKT-005/006 merged; additive migration |
| TKT-008 | P2 | As an operator, cover admin/bulk change paths and define audit retention | 5 | Unscheduled | Needs refinement | TKT-007; admin workflow policy |
| KB-001 | P2 | As a reader, search and page through all knowledge articles | 3 | 9 | Done (#200) | Existing search workflow |
| KB-002 | P2 | As an author/staff member, edit articles with enforced permissions | 5 | Baseline | Existing implementation verified | Author/staff policy in views and tests |
| DATA-001 | P2 | As a maintainer, safely migrate requestor strings to user relations | 8 | Unscheduled | Needs discovery | Mapping/deleted-user policy |
| CMDB-001 | P2 | As an operator, validate asset identifiers and required fields | 5 | Unscheduled | Needs refinement | Existing-data audit |
| PRJ-001 | P2 | As a project owner, receive a redirect after valid creation and useful detail feedback | 3 | 10 | Done (#201) | Workflow audit complete |
| PRJ-002 | P2 | As a project owner, choose dates with native controls and reject reversed schedules | 3 | 11 | In review | PRJ-001 merged |
| UI-001 | P2 | As a maintainer, remove remaining tracked OS artifacts | 1 | 5 carryover | Ready | Usage audit |
| UI-002 | P2 | As a user, use date inputs without obsolete runtime assets | 5 | 5 carryover | Needs discovery | Date parsing/browser audit |
| OPS-001 | P2 | As an operator, follow tested backup/restore and production setup instructions | 5 | Unscheduled | Needs refinement | Deployment/storage choices |
| API-001 | P3 | As an integration developer, use scoped authenticated ticket endpoints | 8 | Unscheduled | Discovery only | Access, rate-limit, paid API policy |

## Definition of ready

Before implementation: identify the user outcome, measurable acceptance criteria,
permission boundaries, dependencies, estimate, test approach, and migration needs.
Refine ambiguous policies before implementing writes. Keep future work provisional.

## Backlog maintenance

At sprint planning, select a coherent goal and a realistic point budget based on
actual capacity. During delivery, move items through Ready → In progress → In
review → Done; Blocked records a reason and next action. Done means merged with
passing checks, not merely implemented. Reference PRs in sprint evidence. New
security/build defects take priority and displace named scope explicitly.
