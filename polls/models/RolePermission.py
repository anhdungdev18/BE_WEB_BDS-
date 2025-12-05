from django.db import models
from .User import User
from .Permission import Permission
from .Role import Role

class RolePermission(models.Model):
    role = models.ForeignKey('Role', on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('role', 'permission')

    def __str__(self):
        return f"{self.role.role_name} - {self.permission.ten_quyen}"