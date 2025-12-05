from django.db import models
from .User import User 


class PostHistory(models.Model):
    CHANGE_TYPE_CHOICES = [
        ('update', 'Update'),
        ('status_change', 'Status Change'),
        ('delete', 'Delete'),
    ]

    post = models.ForeignKey('Post', on_delete=models.CASCADE, related_name='history')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='post_changes')
    old_content = models.TextField()
    new_content = models.TextField(null=True, blank=True)
    change_type = models.CharField(max_length=50, choices=CHANGE_TYPE_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} {self.change_type} bài {self.post} lúc {self.timestamp}"
