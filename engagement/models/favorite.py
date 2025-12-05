from django.db import models
from django.conf import settings  # nếu không dùng nữa có thể xóa import này

class UserFavorite(models.Model):
    # Microservice style: chỉ lưu id thô
    user_id = models.CharField(max_length=9)
    post_id = models.CharField(max_length=9)

    created_at = models.DateTimeField(auto_now_add=True, db_column="ngay_tao")

    class Meta:
        unique_together = ("user_id", "post_id")
        indexes = [
            models.Index(fields=["user_id"]),
            models.Index(fields=["post_id"]),
        ]

    def __str__(self):
        return f"{self.user_id} yêu thích bài {self.post_id} lúc {self.created_at}"
