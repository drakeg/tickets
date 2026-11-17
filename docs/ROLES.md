# Team roles and access-control delivery

Priority: P1. Module enforcement is delivered incrementally; Module enforcement through Sprint 16C is merged (#212).

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

The admin interface honors model permissions. All ticket lists, queues, detail
and local search require view_issue. Creation requires view_issue, add_issue and
view_priority; triage requires view_issue, change_issue and view_priority; ticket-to-article conversion requires view_issue, view_article and
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

Ticket navigation and dashboard counters require view_issue; creation links use
the same three grants as the backend. Denied dashboard requests do not query ticket
counts. Anonymous ticket requests redirect to login and authenticated denials return
403 before looking up records or constructing forms. Assignment and staff status
do not substitute for model grants. Users without grants need an administrator to
assign a role explicitly; registration grants no role.

Project lists, personal/unassigned queues, details and local search require
view_project. Creation requires view_project plus add_project. Project navigation
and dashboard counts follow view_project; denied requests issue no project count
query. Project tasks have model grants for future workflows but no separate task
application routes today; Django admin continues to check model permissions.

Knowledge lists, detail and search require view_article. Creation requires both
view_article and add_article. Ticket conversion requires view_issue, view_article
and add_article, including when redirecting to an existing linked article.
Editing requires view_article plus change_article AND author/staff eligibility;
deletion requires view_article plus delete_article AND author/staff eligibility.
The UI checks each action separately; superusers can recover any article. No
named default group receives change_article or delete_article. Even an author
needs the relevant explicit grant; staff status alone does not grant model access.
To allow a technician to maintain their own articles, assign change_article
deliberately. To moderate other authors' articles, grant staff plus the relevant
model permissions. No new group grants are silently introduced.

These boundaries cover the existing inventory, ticket, project, knowledge and
global-search app routes. RBAC-003 remains the next verification/administration
increment. Permissions are global within each model, not tenant/team/record scopes;
article ownership still compares a legacy author-name string and is additionally
restricted by grants. Username-to-author relation migration, self-service policy,
and audit-retention policy remain separate backlog work. No users are auto-enrolled
or elevated. Registered users see guidance to ask an administrator for a team role.

## P1 delivery sequence

### Sprint 15: RBAC-001 — Role foundation (complete, #209)

Create the named defaults and idempotent setup command, document the matrix and
limits, and test exact meaningful boundaries, repeat runs, dry-run, custom grant
preservation, unchanged users and missing-permission failure. No schema migration.

### Sprint 16A: RBAC-002A — Inventory and global search (complete, #210, 5 points)

First split of the enforcement epic. Acceptance: all inventory entry points enforce
the grants above, reference choices need view grants, denied counts/navigation stay
hidden, global search cannot disclose unauthorized records, and next-request role
revocation plus combined roles behave correctly. Preserve superuser access.

### Sprint 16B: RBAC-002B — Ticket enforcement (complete, #211, 5 points)

Enforce the ticket rules above on GET and POST, hide counts/links consistently,
and verify role defaults, no-role/anonymous denial, missing reference/view grants,
revocation, multi-role union and superuser recovery. Ticket editing retains its
transactional history and CSRF behavior; no new grants or schema changes.

### Sprint 16C: RBAC-002C — Project/article enforcement (complete, #212, 5 points)

Protect all existing project/article app reads and writes with the grants above,
including article management and ticket conversion. Gate navigation and counters,
avoid denied model queries and require destination view permissions. Eleven new
request regressions cover all groups, anonymous/no-role users, write-only grants,
author/staff restrictions, denied mutations, CSRF, next-request revocation/union
and superuser recovery. Preserve authorship and existing content. No migration,
new default grant or automatic membership. See detailed sprint plan for rollback.

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

## Reviewing access in the application (Sprint 17, in review)

Select your username in the top bar to see your own groups and effective workspace
capabilities. The summary combines all group and direct grants, requiring the
same grant combinations as the existing routes. It does not promise per-record
access: article editing/deletion also needs author/staff eligibility. The old fake
profile settings, password form and logout tabs are removed; the shared sign-out
button continues to use protected POST. No credential change is performed.

**Team roles** appears in the administration sidebar only for staff with
auth.view_group. It is read-only and independently enforces both requirements.
It shows actual configured group grants and compares named defaults to
accounts/roles.py, including missing default groups. Missing grants do not
automatically get repaired; additional grants are preserved and may widen access.
Custom groups have no default comparison. These are group-only capabilities;
users may gain more from other memberships/direct grants or superuser status.

Links to edit groups require auth.change_group; a link to review user memberships
requires auth.view_user. Those native admin pages independently enforce their
permissions. This page grants nothing, edits no membership and lists no users.
Existing Django admin logging records actual administration changes.

Verification: review default matrix, deliberately modify a test group's grants
in admin, confirm missing/additional entries, then inspect a nonstaff test user's
profile and authorized app routes. Remove a role and repeat the request to verify
revocation. Do not modify production memberships merely to exercise the page.
No setup command runs while browsing and no new admin permissions are assigned.
