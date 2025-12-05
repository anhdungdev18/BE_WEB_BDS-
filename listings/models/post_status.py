from django.db import models

class PostStatus(models.Model):
    name = models.CharField(max_length=50, unique=True)      # Visible / Hidden / Deleted
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        #db_table = "post_statuses"             # GIỮ nguyên tên bảng cũ
        verbose_name = "Post Status"
        verbose_name_plural = "Post Statuses"

    def __str__(self):
        return self.name
