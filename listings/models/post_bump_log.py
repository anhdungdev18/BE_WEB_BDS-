# listings/models/post_bump_log.py

from django.db import models


class PostBumpLog(models.Model):
    """
    Log mỗi lần user đẩy tin (bump).
    Dùng để giới hạn số lần bump/ngày theo role (MEMBER / AGENT).
    """

    # Không bắt buộc phải có FK cứng, nhưng ORM dùng FK cho tiện.
    # db_constraint=False để không ép ràng buộc ở DB – hợp với hướng microservice.
    post = models.ForeignKey(
        "listings.Post",
        on_delete=models.DO_NOTHING,
        db_column="post_id",
        related_name="bump_logs",
        db_constraint=False,
    )

    actor_id = models.CharField(max_length=9)   # id user đã bump (trùng user_id)
    is_agent = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    note = models.CharField(max_length=255, blank=True, null=True)

    class Meta:

        indexes = [
            models.Index(fields=["post", "created_at"]),
            models.Index(fields=["actor_id", "created_at"]),
        ]

    def __str__(self):
        return f"Bump {self.post_id} by {self.actor_id} at {self.created_at}"
