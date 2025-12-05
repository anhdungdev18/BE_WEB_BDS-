from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class PostRating(models.Model):
    user_id = models.CharField(max_length=9, db_index=True)
    post_id = models.CharField(max_length=9, db_index=True)

    score = models.SmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        db_column="diem",
        default=1,  # để tránh bị hỏi default khi add field
    )
    # comment OPTIONAL -> cho phép null
    comment = models.TextField(
        blank=True,
        null=True,               # quan trọng: cho phép NULL ở DB
        db_column="binh_luan",
    )

    created_at = models.DateTimeField(auto_now_add=True, db_column="ngay_tao")
    updated_at = models.DateTimeField(auto_now=True, db_column="ngay_sua")

    class Meta:

        unique_together = ("user_id", "post_id")
        indexes = [
            models.Index(fields=["post_id"]),
            models.Index(fields=["user_id"]),
        ]

    def __str__(self):
        return f"{self.user_id} chấm {self.score} sao cho bài {self.post_id}"
