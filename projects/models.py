import datetime
from .middleware import get_current_user

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class Task(models.Model):
	description = models.CharField(max_length=100)
	start_date = models.DateTimeField()
	end_date = models.DateTimeField()

class Project(models.Model):
	requestor_name = models.CharField(max_length=50)
	description = models.CharField(max_length=100)
	pub_date = models.DateTimeField('date_published')
	start_date = models.DateTimeField()
	end_date = models.DateTimeField()
	assigned = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
	task = models.ForeignKey(Task, on_delete=models.CASCADE)

	def __str__(self):
		return self.requestor_name
