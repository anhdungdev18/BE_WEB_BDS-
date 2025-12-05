from django.db import models

class Permission(models.Model):
    ten_quyen = models.CharField(max_length=100, unique=True)
    mo_ta     = models.TextField(blank=True)
    code      = models.CharField(max_length=100, unique=True)

    class Meta:
        #db_table = "polls_permission"  # tên mặc định trước đây của app polls
        verbose_name = "Permission"
        verbose_name_plural = "Permissions"

    def __str__(self):
        return self.ten_quyen
