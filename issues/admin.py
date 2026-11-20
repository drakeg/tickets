from django.contrib import admin
from django.db import transaction
from django.core.exceptions import PermissionDenied

from .models import Issue, IssueChange, Priority
from .services import bulk_update_ticket_status, triage_snapshot


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    actions = ('close_selected_tickets', 'reopen_selected_tickets')

    def _change_status(self, request, queryset, is_open):
        if not self.has_change_permission(request):
            raise PermissionDenied
        changed = bulk_update_ticket_status(queryset, is_open, request.user)
        self.message_user(
            request, f'{changed} ticket(s) updated; unchanged tickets skipped.',
        )

    @admin.action(description='Close selected tickets', permissions=['change'])
    def close_selected_tickets(self, request, queryset):
        self._change_status(request, queryset, False)

    @admin.action(description='Reopen selected tickets', permissions=['change'])
    def reopen_selected_tickets(self, request, queryset):
        self._change_status(request, queryset, True)

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        # The admin form has already applied its values to obj. Read the
        # persisted row before saving so the audit records the actual transition.
        before = None
        if change:
            stored = Issue.objects.select_for_update().get(pk=obj.pk)
            before = triage_snapshot(stored)

        super().save_model(request, obj, form, change)

        if before is not None:
            after = triage_snapshot(obj)
            if before != after:
                IssueChange.objects.create(
                    issue=obj,
                    actor=request.user,
                    actor_name=request.user.get_username(),
                    before=before,
                    after=after,
                )


admin.site.register(Priority)
