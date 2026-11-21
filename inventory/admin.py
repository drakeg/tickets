from django.contrib import admin, messages
from django.db import IntegrityError
from django.shortcuts import redirect

from .forms import (
    IDENTITY_CONFLICT_MESSAGE, ServerAdminForm, is_identity_conflict,
)
from .models import Cluster, Operating_System, Server, Vendor


@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    form = ServerAdminForm

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        try:
            return super().changeform_view(
                request, object_id=object_id, form_url=form_url,
                extra_context=extra_context,
            )
        except IntegrityError as error:
            if not is_identity_conflict(error):
                raise
            # The admin's atomic transaction has exited and rolled back.
            # Reopening the form ensures the now-existing name is revalidated.
            self.message_user(request, IDENTITY_CONFLICT_MESSAGE, level=messages.ERROR)
            return redirect(request.path)


admin.site.register(Vendor)
admin.site.register(Cluster)
admin.site.register(Operating_System)
