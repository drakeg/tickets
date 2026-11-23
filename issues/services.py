from django.db import transaction

from .forms import IssueTriageForm
from .models import Issue, IssueChange


def triage_snapshot(issue):
    return {
        'status': 'Open' if issue.issue_open else 'Closed',
        'priority': {'id': issue.priority_id, 'name': str(issue.priority)},
        'assigned': {
            'id': issue.assigned_id,
            'name': str(issue.assigned) if issue.assigned_id else 'Unassigned',
        },
    }


@transaction.atomic
def update_ticket(issue_id, data, actor):
    # Re-read under the transaction so events describe the state being replaced.
    issue = Issue.objects.select_for_update().get(pk=issue_id)
    before = triage_snapshot(issue)
    form = IssueTriageForm(data, instance=issue)
    if form.is_valid():
        updated = form.save(commit=False)
        after = triage_snapshot(updated)
        if before != after:
            updated.save(update_fields=['issue_open', 'priority', 'assigned'])
            IssueChange.objects.create(
                issue=updated, actor=actor, actor_name=actor.get_username(),
                before=before, after=after,
            )
    return form


@transaction.atomic
def bulk_update_ticket_status(queryset, is_open, actor):
    """Change selected ticket statuses and atomically record every transition."""
    changed = 0
    for issue in queryset.order_by('pk').select_for_update().select_related(
        'priority', 'assigned',
    ):
        if issue.issue_open == is_open:
            continue
        before = triage_snapshot(issue)
        issue.issue_open = is_open
        after = triage_snapshot(issue)
        issue.save(update_fields=['issue_open'])
        IssueChange.objects.create(
            issue=issue, actor=actor, actor_name=actor.get_username(),
            before=before, after=after,
        )
        changed += 1
    return changed


@transaction.atomic
def claim_unassigned_ticket(issue_id, actor):
    """Assign an open, unassigned ticket; record its first owner atomically.

    Return False if another agent has already taken the ticket, or if closed.
    The caller must enforce view_issue and change_issue permissions.
    """
    issue = Issue.objects.select_for_update().select_related(
        'priority', 'assigned',
    ).get(pk=issue_id)
    if not issue.issue_open or issue.assigned_id is not None:
        return False
    before = triage_snapshot(issue)
    issue.assigned = actor
    after = triage_snapshot(issue)
    issue.save(update_fields=['assigned'])
    IssueChange.objects.create(
        issue=issue, actor=actor, actor_name=actor.get_username(),
        before=before, after=after,
    )
    return True


@transaction.atomic
def release_own_ticket(issue_id, actor):
    """Return an open ticket owned by actor to the unassigned queue.

    Never remove another user's assignment, even with change_issue permission.
    """
    issue = Issue.objects.select_for_update().select_related(
        'priority', 'assigned',
    ).get(pk=issue_id)
    if not issue.issue_open or issue.assigned_id != actor.pk:
        return False
    before = triage_snapshot(issue)
    issue.assigned = None
    after = triage_snapshot(issue)
    issue.save(update_fields=['assigned'])
    IssueChange.objects.create(
        issue=issue, actor=actor, actor_name=actor.get_username(),
        before=before, after=after,
    )
    return True
