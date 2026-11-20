# ServDesk agent and contributor instructions

Scope: **only** `drakeg/tickets`. Use [Mad Mallard Repository Standards](https://github.com/drakeg/madmallard-repository-standards) as a reference, never as an automatic cross-repository dependency.

## Operating approach

1. Read README, docs/SPRINTS.md, docs/BACKLOG.md, CONTRIBUTING.md, RELEASES.md, SECURITY.md and the GitHub Actions workflows before changing code.
2. Prioritize fixing broken workflows, security and customer-blocking defects, then implement the highest ready backlog story. Continue Build → Deploy → Test → Fix → Redeploy → Continue within an authorized session.
3. Work on focused feature branches and reviewable PRs, preserve protected branches, avoid force pushing, and report actual test/CI/deployment evidence with PR URLs. Never claim local Docker ran without execution evidence.
4. Run Django unit tests, system checks, migration drift checks, Docker Compose config/build/smoke as available, then review CodeQL. Preserve `tickets_data` volume; never use `docker compose down -v` on a working instance without explicit authorization.
5. Use `.env` for developer overrides; never commit secrets or credentials. Bind LAN testing only on trusted networks, configure `DJANGO_ALLOWED_HOSTS`, and do not expose Django's development server to the public internet.
6. Keep sprint/backlog, release policy, documentation and tests synchronized. Backlog 'Done' means merged and validated, not merely a PR opened. Route legitimate contributions into the sprint or prioritized backlog.
7. Badges belong immediately under the README H1 inside `madmallard-badges` markers. Verify versions from manifests, Dockerfile, Compose and workflow files. Use live CI/security/issues/PR badges. Do not fabricate a release, license, test result or deployment.
8. For commercial scope, prioritize independent small IT support teams and MSPs with a demonstrable ticket/asset/knowledge workflow; measure real setup time, agent feedback and willingness to pay before claiming market validation.
9. Keep this repository independent from all other products. Do not alter unrelated repositories, services, credentials or shared databases.
10. Follow the existing issue authorization, change-history and transaction semantics; obtain explicit policy before destructive data migrations, automatic audit purges or customer-data deletion.

## Current delivery state

Sprint 18B audited bulk ticket status actions: complete (#217).
Sprint 19A standards/README/agent/release/CI validation: independent PR.
Next: isolate and prove a backup/restore rehearsal, then validate an SMB operator demo.

## Badge validation

Run `python scripts/check_repo_standards.py` and keep the check in GitHub Actions. Badge maintenance happens in normal technology, workflow, license and release PRs.
