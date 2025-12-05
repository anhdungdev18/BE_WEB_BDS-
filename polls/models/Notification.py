from django.db import models
from .User import User
class Notification(models.Model):
    TYPE_CHOICES = [
        ('post_approved', 'Bài đăng được duyệt'),
        ('new_message', 'Tin nhắn mới'),
        # thêm loại thông báo khác nếu cần
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, null=True, blank=True)
    title = models.CharField(max_length=255)
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    def mark_as_read(self):
        """Đánh dấu thông báo là đã đọc"""
        if not self.is_read:
            self.is_read = True
            from django.utils import timezone
            self.read_at = timezone.now()
            self.save()

    def __str__(self):
        return f"{self.title} ({'Đã đọc' if self.is_read else 'Chưa đọc'})"
