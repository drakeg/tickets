from django.contrib import admin

from .forms import ServerAdminForm
from .models import Cluster, Operating_System, Server, Vendor


@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    form = ServerAdminForm


admin.site.register(Vendor)
admin.site.register(Cluster)
admin.site.register(Operating_System)
