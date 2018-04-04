from django.contrib import admin

from .models import Server
from .models import Vendor
from .models import Cluster
from .models import Operating_System

admin.site.register(Server)
admin.site.register(Vendor)
admin.site.register(Cluster)
admin.site.register(Operating_System)
