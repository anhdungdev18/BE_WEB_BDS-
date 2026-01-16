from django.conf import settings
from django.db import models
import uuid


class Notification(models.Model):
    TYPE_MESSAGE = "message"
    TYPE_COMMENT = "comment"
    TYPE_FAVORITE = "favorite"
    TYPE_POST_STATUS = "post_status"
    TYPE_MEMBERSHIP = "membership"
    TYPE_POST_BUMP = "post_bump"

    TYPE_CHOICES = [
        (TYPE_MESSAGE, "Message"),
        (TYPE_COMMENT, "Comment"),
        (TYPE_FAVORITE, "Favorite"),
        (TYPE_POST_STATUS, "Post Status"),
        (TYPE_MEMBERSHIP, "Membership"),
        (TYPE_POST_BUMP, "Post Bump"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    actor_id = models.CharField(max_length=9)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True, null=True)
    target_type = models.CharField(max_length=32, blank=True, null=True)
    target_id = models.CharField(max_length=64, blank=True, null=True)
    extra = models.JSONField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "is_read", "-created_at"]),
            models.Index(fields=["type"]),
        ]

    def __str__(self):
        return f"{self.user_id} <- {self.type}"
