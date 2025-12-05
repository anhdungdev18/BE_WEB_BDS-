from django.db import models
from django.contrib.auth.models import AbstractUser
class ApprovalStatus(models.Model):
    name = models.CharField(max_length=50, unique=True)   # Ví dụ: Pending, Approved, Rejected
    description = models.TextField(blank=True, null=True) # Mô tả chi tiết (nếu cần)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'approval_statuses'  # Tên bảng trong database
        verbose_name = 'Approval Status'
        verbose_name_plural = 'Approval Statuses'

    def __str__(self):
        return self.name
