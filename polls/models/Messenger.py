from django.db import models
from .User import User as MyUser


class Messenger(models.Model):
    nguoi_gui = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='sent_messages')
    nguoi_nhan = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='received_messages')
    noi_dung = models.TextField()
    thoi_gian = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    def __str__(self):
        return f"Từ {self.nguoi_gui} tới {self.nguoi_nhan} lúc {self.thoi_gian}"
