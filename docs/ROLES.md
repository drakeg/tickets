# Team roles and access-control delivery

Priority: P1. This is an active delivery epic, not a completed security boundary.

## Default groups

| Capability | Infrastructure Team | Help Desk | Project Manager |
|---|---|---|---|
| Inventory systems/OS/vendors/clusters | View, add, change | View | No default grant |
| Tickets | View, change | View, add, change | View |
| Priority catalog | View | View | View |
| Projects | View | View | View, add, change |
| Project tasks | No default grant | No default grant | View, add, change |
| Knowledge articles | View, add | View, add | View, add |
| Delete records | No default grant | No default grant | No default grant |
| Manage users/groups/permissions | No default grant | No default grant | No default grant |

These are Django model-level grants, global within the site, not per-record or
per-assignee restrictions. Memberships combine permissions using Django's normal
union behavior. Superusers retain full access. Existing custom grants are not
revoked by setup and may widen a group's access beyond the default matrix.

## Setup and assignment

After migrations, preview then apply:

```bash
docker compose exec web python manage.py setup_roles --dry-run
docker compose exec web python manage.py setup_roles
```

Setup creates missing groups and adds missing default grants. It can be rerun
without duplicating groups or removing custom permissions. It never assigns users,
changes passwords, or sets staff/superuser flags. Missing model permissions stop
setup before any groups are written. The command uses an atomic transaction.

Administrators assign roles through **Administration → Users → Groups**. Group
membership does not grant admin-site access: that separately requires is_staff.
Do not make users staff simply to use ordinary app pages. If admin-site access is
needed, assign staff status deliberately; model permissions still govern its forms.
No group receives user/group management or delete permissions by default.

## What is enforced today

The admin interface honors model permissions. Ticket triage requires
issues.change_issue; ticket-to-article conversion requires view_issue and
add_article. Inventory lists/detail/name search require view_server; the operating
system route requires view_operating_system. System creation requires view_server,
add_server, and view grants for OS/vendor/cluster choices. Vendor creation requires
view_vendor and add_vendor instead of staff status. Infrastructure members therefore
use normal application forms without admin-site access.

Inventory navigation/counts are hidden without view_server. Add system appears
only with all required grants; direct URLs independently enforce them. Anonymous
inventory requests redirect to login; authenticated denial returns a useful 403.
Global search is now a permission-filtered query over tickets, projects, inventory
and knowledge articles, capped at 10 results per authorized section. No denied
model is queried or returned. It requires login and at least one view grant.

This is not yet full application RBAC: direct ticket/project/article read routes,
most of their create flows, and their dashboard counters retain the existing
policy. Article editing/deletion still uses author/staff rules. Those domain gaps
remain the next P1 increments; do not interpret the matrix as a universal deny
policy until that work is complete. No users are auto-enrolled or elevated.

## P1 delivery sequence

### Sprint 15: RBAC-001 — Role foundation (complete, #209)

Create the named defaults and idempotent setup command, document the matrix and
limits, and test exact meaningful boundaries, repeat runs, dry-run, custom grant
preservation, unchanged users and missing-permission failure. No schema migration.

### Sprint 16A: RBAC-002A — Inventory and global search (in review, 5 points)

First split of the enforcement epic. Acceptance: all inventory entry points enforce
the grants above, reference choices need view grants, denied counts/navigation stay
hidden, global search cannot disclose unauthorized records, and next-request role
revocation plus combined roles behave correctly. Preserve superuser access.

### Sprint 16B/C: RBAC-002 — Remaining module enforcement (next P1)


- Replace public/module reads and login-only writes with explicit model grants.
- Cover list, detail, search, create, update, dashboard aggregates and global search.
- Make navigation reflect backend permissions while direct URLs enforce them.
- Login redirects anonymous users; authenticated users without grants receive 403.
- Preserve superuser recovery/admin access and POST/CSRF protections.
- Add real request tests for each group, a no-role user, anonymous users and a
  multi-role user. Verify direct URLs and search/aggregate output, not just menus.
- Reconcile vendor staff-only and article author/staff policies with model grants;
  keep authorship stable. Do not silently enable deletion or user administration.
- Do not automatically assign roles to existing users or publicly registered users.

### RBAC-003 — Permission administration and verification (P1 follow-up, 5 points)

Document staff versus app roles, verify role changes take effect on the next
request, test revocation and combined groups, and add an operator-facing matrix.
Existing Django admin logging records group/membership administration. Evaluate
record-level ownership and self-service access separately before promising them.

## Review / rollback

Review by creating a non-staff test user, assigning Help Desk, and verifying that
it can open ticket triage but cannot access Django admin. The foundation adds no
user membership and needs no database schema changes. Removing a configured group
would remove its granted capabilities from members; setup intentionally does not
delete groups or reconcile custom grants destructively.
