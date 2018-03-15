import datetime

from django.db import models
from django.utils import timezone

class Issue(models.Model):
	requestor_name = models.CharField(max_length=50)
	description = models.CharField(max_length=500)
	pub_date = models.DateTimeField('date_published')
	assigned = models.CharField(max_length=50)
	def __str__(self):
		return self.requestor_name
