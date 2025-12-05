from django.db import models

class RolePermission(models.Model):
    role = models.ForeignKey("accounts.Role", on_delete=models.CASCADE)
    permission = models.ForeignKey("accounts.Permission", on_delete=models.CASCADE)

    class Meta:
        
        unique_together = ("role", "permission")

    def __str__(self):
        # permission có field ten_quyen theo code cũ
        return f"{self.role.role_name} - {self.permission.ten_quyen}"
