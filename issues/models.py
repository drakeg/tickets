import datetime
from .middleware import get_current_user

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class Priority(models.Model):
    name = models.CharField(max_length=50)
    def __str__(self):
        return self.name

class Issue(models.Model):
    requestor_name = models.CharField(max_length=50, default=get_current_user())
    summary = models.CharField(max_length=50)
    description = models.CharField(max_length=500)
    priority = models.ForeignKey(Priority, on_delete=models.CASCADE)
    pub_date = models.DateTimeField('date_published')
    assigned = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    issue_open = models.BooleanField(default="True")
    def __str__(self):
        return self.requestor_name
