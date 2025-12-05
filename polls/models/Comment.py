from django.db import models
from .User import User 
from .Post import Post

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    # nếu là reply thì parent trỏ tới comment cha, null nếu là comment gốc. 
    is_deleted = models.BooleanField(default=False)  # đánh dấu comment đã bị xóa
    def soft_delete(self):
        self.is_deleted = True
        self.save()
    def __str__(self):
        return f"{self.user} bình luận bài {self.post} lúc {self.created_at}"
