from django.db import models
from django.utils import timezone
from .Permission import Permission
from django.contrib.auth.hashers import make_password, check_password
# role cho user: admin, user 
class Role(models.Model):
    role_name = models.CharField(max_length=200, unique=True)
    mo_ta = models.TextField(blank=True, null=True)
    permissions = models.ManyToManyField(Permission, related_name='roles', through='RolePermission')
    def __str__(self):
        return self.role_name  