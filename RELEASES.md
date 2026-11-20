# ServDesk release policy

ServDesk is under active development. No published SemVer version is assumed here; verify tags and GitHub Releases before declaring a release.

## Semantic versioning

- **MAJOR**: incompatible user/API, data-format, permission, configuration or upgrade change that requires deliberate migration.
- **MINOR**: backward-compatible customer-visible capability such as a new audited ticket workflow.
- **PATCH**: backward-compatible defect, security or reliability correction.
- **Pre-1.0**: use `v0.x.y` for pilots if useful; changing a documented migration contract still requires an explicit warning.

A merged PR or completed sprint alone does not require a release. Release when a tested, meaningful group of changes is ready for an operator or pilot.

## Release checklist

1. Confirm scope and accepted backlog stories; review changelog/user impact and backward compatibility.
2. Run Django checks, migrations drift, full test suite, Docker Compose checks, and review GitHub CI and CodeQL results.
3. Rehearse backup/restore for any data migration in an isolated environment. Never modify the real `tickets_data` volume to test a release.
4. Verify configuration, access restrictions, security dependencies, docs, README badges and runbook.
5. Tag the verified commit using `vMAJOR.MINOR.PATCH`, publish a GitHub Release with rollback and migration instructions, and only then add a dynamic release badge.
6. Validate deployment and at least one complete ticket create/triage/knowledge lookup workflow in the target test environment.

## Rollback

Revert application changes only after assessing any additive schema migrations and preserved data. Keep audit history and backups intact. Do not automatically purge data or run destructive downgrades.

## Pilot readiness

Before a priced SMB pilot, verify a LAN-accessible demo, backups, staff/role setup and a realistic agent workflow. Pricing and willingness-to-pay hypotheses remain unvalidated until actual conversations.
