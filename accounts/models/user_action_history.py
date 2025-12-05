from django.db import models
from django.conf import settings

class UserActionHistory(models.Model):
    ACTION_CHOICES = [
        ("like", "Like"),
        ("share", "Share"),
        ("comment", "Comment"),
        # có thể bổ sung: ("view","View"), ("save","Save"), ...
    ]

    # Tránh import vòng: dùng AUTH_USER_MODEL
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="actions",
    )

    # Trỏ sang Post ở app listings bằng chuỗi để tránh vòng import
    # Giữ tên field 'bai_dang' như code cũ; nếu bảng cũ có cột 'bai_dang_id' thì giữ db_column cho chắc
    bai_dang = models.ForeignKey(
        "listings.Post",
        on_delete=models.CASCADE,
        related_name="user_actions",
        db_column="bai_dang_id",   # nếu DB chưa có bảng cũ, có thể bỏ dòng này
    )

    action_type = models.CharField(max_length=50, choices=ACTION_CHOICES)
    timestamp   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} {self.action_type} bài {self.bai_dang} lúc {self.timestamp}"

    class Meta:
        #db_table = "UserActionHistory"   # nếu DB cũ tên khác (vd polls_useractionhistory) thì đổi cho khớp
        pass 