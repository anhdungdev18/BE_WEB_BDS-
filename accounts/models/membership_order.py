# accounts/models/membership_order.py
from django.db import models
from django.conf import settings


class MembershipOrder(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Chờ thanh toán"
        PAID = "PAID", "Đã thanh toán"
        CANCELLED = "CANCELLED", "Đã hủy"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="membership_orders",
    )
    plan = models.ForeignKey(
        "accounts.MembershipPlan",
        on_delete=models.PROTECT,
        related_name="orders",
    )
    amount_vnd = models.BigIntegerField(
        help_text="Số tiền cần thanh toán (VND)",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    bank_ref = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Mã giao dịch ngân hàng (admin nhập tay / webhook)",
    )
    transfer_note = models.CharField(
        max_length=255,
        help_text="Nội dung chuyển khoản dùng để đối soát, ví dụ: UPGRADE_USER_3_ORDER_5",
    )
    qr_image_url = models.URLField(
        max_length=512,
        blank=True,
        null=True,
        help_text="Link ảnh QR VietQR",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        #db_table = "membership_order"          # để SP SQL dùng tên này luôn
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"Order #{self.pk} - user {self.user_id} - {self.status}"
