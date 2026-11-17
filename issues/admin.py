from django.contrib import admin
from django.db import transaction

from .models import Issue, IssueChange, Priority
from .services import triage_snapshot


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
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
