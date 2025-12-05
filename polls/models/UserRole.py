from django.db import models
from django.utils import timezone
from .User import User
from .Role import Role

class UserRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='role_users')
    assigned_at = models.DateTimeField(default=timezone.now)  # thời điểm cấp vai trò
    expires_at = models.DateTimeField(null=True, blank=True)  # hết hạn (nếu có)
    is_active = models.BooleanField(default=True)  # còn hiệu lực không
    granted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='granted_roles'
    )  # ai là người cấp (admin hoặc hệ thống)

    class Meta:
        unique_together = ('user', 'role')
        db_table = 'user_role'
        verbose_name = 'Phân quyền người dùng'
        verbose_name_plural = 'List phân quyền người dùng'

    def __str__(self):
        return f"{self.user.ho_ten} - {self.role.role_name}"

    # ✅ Kiểm tra role còn hiệu lực
    def is_valid(self):
        if not self.is_active:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return True
