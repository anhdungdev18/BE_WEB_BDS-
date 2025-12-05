from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        #db_table = "polls_category"  # đổi nếu bảng cũ tên khác
        pass
    def __str__(self):
        return self.name
