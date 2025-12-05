from django.db import models
from django.utils import timezone
from django.conf import settings

class UserRole(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_roles",
    )
    role = models.ForeignKey(
        "accounts.Role",
        on_delete=models.CASCADE,
        related_name="role_users",
    )
    assigned_at = models.DateTimeField(default=timezone.now)
    expires_at  = models.DateTimeField(null=True, blank=True)
    is_active   = models.BooleanField(default=True)
    granted_by  = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="granted_roles",
    )

    class Meta:
        # db_table = "user_role"   # GIỮ đúng như code cũ của huynh
        unique_together = ("user", "role") # 1 user chỉ có 1 role nhất định
        verbose_name = "Phân quyền người dùng"
        verbose_name_plural = "List phân quyền người dùng"

    def __str__(self):
        # User hiện không có ho_ten -> dùng email/username cho chắc
        u = getattr(self.user, "email", None) or getattr(self.user, "username", "user")
        return f"{u} - {self.role.role_name}"

    def is_valid(self):
        return self.is_active and (not self.expires_at or timezone.now() <= self.expires_at)
