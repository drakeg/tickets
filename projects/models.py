import datetime
from .middleware import get_current_user

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class Task(models.Model):
    summary = models.CharField(max_length=25)
    description = models.CharField(max_length=100)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    def __str__(self):
        return self.summary

class Project(models.Model):
    requestor_name = models.CharField(max_length=50, default=get_current_user())
    summary = models.CharField(max_length=25)
    description = models.CharField(max_length=100)
    pub_date = models.DateTimeField('date_published')
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    assigned = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)

    def __str__(self):
        return self.requestor_name
