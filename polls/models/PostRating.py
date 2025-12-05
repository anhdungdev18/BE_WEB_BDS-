from django.db import models
from .User import User 
from .Post import Post

class PostRating(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings')
    rating = models.SmallIntegerField()  # ví dụ 1-5
    comment = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')  # mỗi user chỉ được đánh giá 1 lần cho mỗi bài

    def __str__(self):
        return f"{self.user} đánh giá {self.rating} sao cho bài {self.post}"
