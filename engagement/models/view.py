from django.db import models


class PostView(models.Model):
    # user_id có thể null nếu guest
    user_id = models.CharField(max_length=9, null=True, blank=True, db_index=True)
    post_id = models.CharField(max_length=9, db_index=True)

    session_id = models.CharField(max_length=64, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_column="ngay_xem")

    class Meta:

        indexes = [
            models.Index(fields=["post_id"]),
            models.Index(fields=["user_id"]),
        ]

    def __str__(self):
        return f"{self.user_id or 'guest'} xem bài {self.post_id} lúc {self.created_at}"
