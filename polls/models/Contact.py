from django.db import models
from .User import User 
from .Post import Post

class LienHe(models.Model):
    bai_dang = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='lien_he')
    nguoi_lien_he = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lien_he')
    noi_dung = models.TextField()
    ngay_lien_he = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Liên Hệ"
        verbose_name_plural = "Liên Hệ"

    def __str__(self):
        return f"{self.nguoi_lien_he} liên hệ bài {self.bai_dang} lúc {self.ngay_lien_he}"
