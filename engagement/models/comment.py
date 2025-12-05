from django.db import models


class PostComment(models.Model):
    STATUS_CHOICES = (
        ("PENDING", "Chờ duyệt"),
        ("APPROVED", "Đã duyệt"),
        ("REJECTED", "Từ chối"),
    )

    user_id = models.CharField(max_length=9, db_index=True)
    post_id = models.CharField(max_length=9, db_index=True)

    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="replies",
        db_column="parent_id",
    )

    content = models.TextField(db_column="noi_dung")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="APPROVED",  # đổi thành PENDING nếu huynh muốn duyệt tay
        db_column="trang_thai",
    )

    created_at = models.DateTimeField(auto_now_add=True, db_column="ngay_tao")
    updated_at = models.DateTimeField(auto_now=True, db_column="ngay_sua")

    class Meta:

        indexes = [
            models.Index(fields=["post_id"]),
            models.Index(fields=["user_id"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"Comment {self.id} của {self.user_id} trên bài {self.post_id}"
