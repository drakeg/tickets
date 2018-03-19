import datetime

from django.db import models
from django.utils import timezone

class Version(models.Model):
	version_no = models.CharField(max_length=25)
	def __str__(self):
		return self.version_no

class Operating_System(models.Model):
	os_name = models.CharField(max_length=50)
	version_no = models.ForeignKey(Version, on_delete=models.CASCADE)

class Vendor(models.Model):
	vendor_name = models.CharField(max_length=50)
	def __str__(self):
		return self.vendor_name

class Cluster(models.Model):
	cluster_name = models.CharField(max_length=50)
	def __str__(self):
		return self.cluster_name

class Server(models.Model):
	server_name = models.CharField(max_length=50)
	os = models.ForeignKey(Operating_System, on_delete=models.CASCADE)
	vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
	cluster = models.ForeignKey(Cluster, on_delete=models.CASCADE)
	pub_date = models.DateTimeField('date_published')
	def __str__(self):
		return self.server_name
	def was_published_recently(self):
		return self.pub_date >= timezone.now() - datetime.timedelta(days=1)
