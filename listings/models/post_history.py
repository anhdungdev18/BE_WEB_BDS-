from django.db import models
from django.conf import settings

class PostHistory(models.Model):
    CHANGE_TYPE_CHOICES = [
        ("update", "Update"),
        ("status_change", "Status Change"),
        ("delete", "Delete"),
    ]

    post = models.ForeignKey("listings.Post", on_delete=models.CASCADE, related_name="history")
    #user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="post_changes")
    actor_id = models.CharField(max_length=9)
    # giữ kiểu Text như code cũ (huynh đã serialize dict thành str)
    old_content = models.TextField()
    new_content = models.TextField(null=True, blank=True)
    change_type = models.CharField(max_length=50, choices=CHANGE_TYPE_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        #db_table = "polls_posthistory"  # đổi nếu bảng cũ tên khác
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.actor_id} {self.change_type} bài {self.post} lúc {self.timestamp}"
