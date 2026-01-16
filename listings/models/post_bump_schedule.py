# listings/models/post_bump_schedule.py

from django.db import models


class PostBumpSchedule(models.Model):
    STATUS_ACTIVE = "active"
    STATUS_PAUSED = "paused"

    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_PAUSED, "Paused"),
    ]

    post = models.ForeignKey(
        "listings.Post",
        on_delete=models.DO_NOTHING,
        db_column="post_id",
        related_name="bump_schedules",
        db_constraint=False,
    )

    owner_id = models.CharField(max_length=9)
    run_time = models.TimeField()
    timezone = models.CharField(max_length=64, default="Asia/Ho_Chi_Minh")
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_ACTIVE)

    last_run_at = models.DateTimeField(null=True, blank=True)
    next_run_at = models.DateTimeField(null=True, blank=True)
    fail_reason = models.CharField(max_length=64, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["owner_id", "is_active"]),
            models.Index(fields=["next_run_at"]),
        ]

    def __str__(self):
        return f"Schedule {self.post_id} at {self.run_time}"
