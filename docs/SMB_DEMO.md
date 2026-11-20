# SMB support workflow — test and pilot checklist

The synthetic role-aware smoke test exercises a small service desk without
creating any records in the operator's existing SQLite volume. It does not
claim customer interviews, usage, revenue, demand or market validation.

## Automated demonstration

```bash
docker compose run --rm test python manage.py test dashboard.test_smb_demo_smoke -v 2
```

The test migrates an isolated test database and provisions the three existing
roles. It creates synthetic tickets, triages status with an audit event, turns a
ticket into a linked knowledge article, and verifies lookup. An Infrastructure
Team user creates and searches an asset, while a Project Manager creates and
searches a project. It verifies that a Help Desk user cannot create inventory
or projects, and anonymous users cannot browse protected modules.

## Manual demo acceptance checklist

- Create a temporary non-production operator and assign roles deliberately.
- Create a ticket, triage and close it; show the audit history.
- Publish a reviewed article from that ticket and find it through search.
- Create and find a system, then create and find a project with correct roles.
- Demonstrate forbidden actions (403) with restricted users.
- Confirm all records are synthetic; remove only the deliberately created demo
  fixtures after verifying they do not overlap any real records.
- Capture setup friction, time-to-first-ticket, and operator feedback.

**Commercialization hypothesis:** a 2–10-agent independent MSP or internal IT
team would value one inexpensive workspace for ticket triage, assets, and
reusable solutions. Validate feature priority and willingness to pay with actual
interviews before choosing a subscription price. No market demand is claimed.
