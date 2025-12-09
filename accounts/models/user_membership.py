# accounts/models/user_membership.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from .membership_plan import MembershipPlan


class UserMembership(models.Model):
    """
    Trạng thái VIP hiện tại của 1 user.
    - Gắn với MembershipPlan (VIP 1 tháng, 3 tháng,...)
    - expired_at > now() thì coi như VIP còn hiệu lực
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="membership",
    )
    plan = models.ForeignKey(
        MembershipPlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user_memberships",
    )
    started_at = models.DateTimeField()
    expired_at = models.DateTimeField()

    # Dùng cho tính năng bump tin (đẩy tin), để sau dùng tiếp
    last_bump_date = models.DateField(null=True, blank=True)
    bumps_used_today = models.PositiveIntegerField(default=0)

    class Meta:
        # db_table = "user_membership"
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["expired_at"]),
        ]

    def __str__(self):
        return f"Membership of user {self.user_id} ({self.plan_id})"

    # ===== Helper =====
    def is_active(self) -> bool:
        return self.expired_at > timezone.now()

    def remaining_days(self) -> int:
        if not self.is_active():
            return 0
        delta = self.expired_at - timezone.now()
        return max(delta.days, 0)

    def extend(self, extra_days: int):
        """
        Gia hạn thêm extra_days ngày.
        Nếu đang hết hạn thì tính từ bây giờ.
        """
        now = timezone.now()
        if self.expired_at and self.expired_at > now:
            self.expired_at = self.expired_at + timedelta(days=extra_days)
        else:
            self.started_at = now
            self.expired_at = now + timedelta(days=extra_days)

    def reset_bump_counter_if_new_day(self):
        """
        Reset số lượt bump/ngày nếu sang ngày mới (dùng sau cho API bump tin).
        """
        today = timezone.localdate()
        if self.last_bump_date != today:
            self.last_bump_date = today
            self.bumps_used_today = 0
