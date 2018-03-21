from .middleware import get_current_user

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class Article(models.Model):
    author = models.CharField(max_length=150)
    description = models.CharField(max_length=150)
    keywords = models.CharField(max_length=100)
    pub_date = models.DateTimeField('date_published')
    def __str__(self):
        return self.author
