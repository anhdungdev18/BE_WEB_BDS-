from django.db import models

class Role(models.Model):
    role_name = models.CharField(max_length=200, unique=True)
    mo_ta     = models.TextField(blank=True, null=True)

    permissions = models.ManyToManyField(
        "accounts.Permission",
        related_name="roles",
        through="accounts.RolePermission",
    )
    class Meta:   
        verbose_name = "Role"
        verbose_name_plural = "Roles"
    def __str__(self):
        return self.role_name
