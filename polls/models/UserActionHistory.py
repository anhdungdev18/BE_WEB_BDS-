from django.db import models
from .User import User 
from .Post import Post 

class UserActionHistory(models.Model):
    ACTION_CHOICES = [
        ('like', 'Like'),
        ('share', 'Share'),
        ('comment', 'Comment'),
        # thêm hành động khác nếu cần
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='actions')
    bai_dang = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='user_actions')
    action_type = models.CharField(max_length=50, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} {self.action_type} bài {self.bai_dang} lúc {self.timestamp}"
