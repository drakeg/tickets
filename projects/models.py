import datetime
from .middleware import get_current_user
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class Task(models.Model):
    summary = models.CharField(max_length=25)
    description = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return self.summary

class Project(models.Model):
    requestor_name = models.CharField(max_length=50, default=get_current_user())
    summary = models.CharField(max_length=25)
    description = models.CharField(max_length=100)
    pub_date = models.DateTimeField('date_published')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    assigned = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.requestor_name
