import string, random
from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings

def generate_unique_id(model, field_name="id", length=9):
    chars = string.ascii_uppercase + string.digits
    while True:
        rid = "".join(random.choices(chars, k=length))
        if not model.objects.filter(**{field_name: rid}).exists():
            return rid

class Post(models.Model):
    id = models.CharField(primary_key=True, max_length=9, editable=False)

    title       = models.CharField(max_length=255)
    description = models.TextField()
    address     = models.JSONField()                         # JSON
    location    = models.JSONField()                         # JSON
    details     = models.JSONField()                         # JSON
    other_info  = models.JSONField(blank=True, null=True)    # JSON

    area  = models.FloatField(validators=[MinValueValidator(0.01)])
    price = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])

    post_type = models.ForeignKey("listings.PostType", on_delete=models.CASCADE, related_name="posts")
    category  = models.ForeignKey("listings.Category", on_delete=models.CASCADE, related_name="posts")

    #user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts")
    owner_id = models.CharField(max_length=9)
    approval_status = models.ForeignKey("listings.ApprovalStatus", on_delete=models.SET_NULL, null=True, related_name="posts")
    post_status     = models.ForeignKey("listings.PostStatus",     on_delete=models.SET_NULL, null=True, related_name="posts")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        #db_table = "polls_post"   # đổi nếu bảng cũ tên khác
        indexes = [
            models.Index(fields=["category"]),
            models.Index(fields=["post_type"]),
            models.Index(fields=["approval_status"]),
            models.Index(fields=["post_status"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        creating = self._state.adding

        # mặc định trạng thái nếu chưa có
        if not self.approval_status:
            from .approval_status import ApprovalStatus
            self.approval_status = ApprovalStatus.objects.filter(name="Pending").first()
        if not self.post_status:
            from .post_status import PostStatus
            self.post_status = PostStatus.objects.filter(name="Hidden").first()

        # gán id nếu chưa có
        if not self.id:
            self.id = generate_unique_id(Post)

        if creating:
            # tạo mới: lưu & thoát (không ghi history)
            super().save(*args, **kwargs)
            return

        # cập nhật: so sánh trước-sau để ghi PostHistory
        from .post_history import PostHistory

        try:
            old = Post.objects.get(pk=self.pk)
        except Post.DoesNotExist:
            # fallback nếu vì lý do gì đó bản cũ không tồn tại
            super().save(*args, **kwargs)
            return

        tracked_fields = [
            "title", "description", "address", "location", "details",
            "other_info", "area", "price", "approval_status_id", "post_status_id"
        ]
        old_content, new_content, changed = {}, {}, False

        for f in tracked_fields:
            old_val = getattr(old, f)
            new_val = getattr(self, f)
            if old_val != new_val:
                changed = True
                old_content[f] = old_val
                new_content[f] = new_val

        # lưu thay đổi
        super().save(*args, **kwargs)

        # ghi lịch sử nếu có
        if changed:
            PostHistory.objects.create(
                post=self,
                actor_id=self.owner_id,
                old_content=str(old_content),
                new_content=str(new_content),
                change_type="update",
            )
