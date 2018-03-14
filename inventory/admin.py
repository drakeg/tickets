from django.contrib import admin

from .models import Server
from .models import Vendor
from .models import Cluster
from .models import Operating_System
from .models import Version

admin.site.register(Server)
admin.site.register(Vendor)
admin.site.register(Cluster)
admin.site.register(Version)
admin.site.register(Operating_System)
