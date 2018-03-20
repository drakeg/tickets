from django.contrib import admin

from .models import Issue
from .models import Priority

admin.site.register(Priority)
admin.site.register(Issue)
