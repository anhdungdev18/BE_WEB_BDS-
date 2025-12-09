# listings/models/post_image.py
from django.db import models

class PostImage(models.Model):
    post = models.ForeignKey(
        "listings.Post",          # dùng tên app + tên model, không phụ thuộc file
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(upload_to="posts/")  # tự upload lên Cloudinary
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:

        ordering = ["-created_at"]

    def __str__(self):
        return f"Image #{self.id} for post {self.post_id}"
