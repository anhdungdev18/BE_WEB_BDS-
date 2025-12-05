# accounts/models/membership_plan.py
from django.db import models


class MembershipPlan(models.Model):
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Mã gói, ví dụ: AGENT_1M, AGENT_3M",
    )
    name = models.CharField(
        max_length=255,
        help_text="Tên gói hiển thị cho người dùng",
    )
    price_vnd = models.BigIntegerField(
        help_text="Giá gói (VND)",
    )
    duration_days = models.PositiveIntegerField(
        help_text="Thời gian hiệu lực (ngày), ví dụ 30, 90, 365",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        #db_table = "membership_plan"           # để SP SQL dùng tên này luôn
        ordering = ["price_vnd"]

    def __str__(self):
        return f"{self.name} ({self.price_vnd} VND / {self.duration_days} ngày)"
