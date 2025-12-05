from django.db import models
from .User import User
from .Post import Post

class UserFavorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    bai_dang = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='favorited_by')
    ngay_tao = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'bai_dang')  # tránh trùng lặp favorite

    def __str__(self):
        return f"{self.user} yêu thích bài {self.bai_dang} lúc {self.ngay_tao}"
