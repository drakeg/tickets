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
