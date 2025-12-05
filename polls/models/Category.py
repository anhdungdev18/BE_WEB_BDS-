from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser

from django.contrib.auth.hashers import make_password, check_password 
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name 