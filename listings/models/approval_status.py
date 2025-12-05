from django.db import models

class ApprovalStatus(models.Model):
    name = models.CharField(max_length=50, unique=True)      # Pending / Approved / Rejected
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        #db_table = "approval_statuses"          # GIỮ nguyên tên bảng cũ
        verbose_name = "Approval Status"
        verbose_name_plural = "Approval Statuses"

    def __str__(self):
        return self.name
