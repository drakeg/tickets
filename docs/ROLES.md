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

The admin interface already honors model permissions. The ticket triage route
requires issues.change_issue, so Help Desk and Infrastructure membership enable
that existing workflow even for non-staff users. Ticket-to-article conversion
requires both issues.view_issue and knowledgebase.add_article; all three default
groups have these grants. Group setup does not change the
rest of the application's current behavior. Most read pages are public, most
creation pages require only login, vendor creation uses staff status, and article
editing uses author/staff rules. A missing grant in this table is therefore not yet
a deny rule for those main-app routes. Group setup alone is not full RBAC.

## P1 delivery sequence

### Sprint 15: RBAC-001 — Role foundation (in review, 3 points)

Create the named defaults and idempotent setup command, document the matrix and
limits, and test exact meaningful boundaries, repeat runs, dry-run, custom grant
preservation, unchanged users and missing-permission failure. No schema migration.

### Sprint 16: RBAC-002 — Enforce module access (next, 8 points; split by domain)

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
