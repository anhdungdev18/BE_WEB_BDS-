from django.db import models
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password 
from .User import User
from .PostType import PostType
from .Category import Category
from .ApprovalStatus import ApprovalStatus
from .PostStatus import PostStatus
from .PostHistory import PostHistory

import string
import random
from django.core.validators import MinValueValidator
# Hàm tạo ID ngẫu nhiên và đảm bảo tính duy nhất
def generate_unique_id(model, field_name='id', length=9):
    chars = string.ascii_uppercase + string.digits
    while True:
        random_id = ''.join(random.choices(chars, k=length))
        if not model.objects.filter(**{field_name: random_id}).exists():
            return random_id
        
class Post(models.Model):
    id = models.CharField(primary_key=True, max_length=9, editable=False)  # ID bài đăng
    title = models.CharField(max_length=255)               # Tiêu đề bài đăng
    description = models.TextField()                       # Mô tả chi tiết
    address = models.JSONField()                           # Địa chỉ BĐS (JSON)
    location = models.JSONField()                          # Vị trí BĐS (JSON)
    details = models.JSONField()                           # Thông tin chi tiết (JSON)
    other_info = models.JSONField(blank=True, null=True)   # Thông tin khác (JSON)
    area = models.FloatField(validators=[MinValueValidator(0.01)])                             # Diện tích
    price = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])  # Giá
    post_type = models.ForeignKey(PostType, on_delete=models.CASCADE, related_name="posts")  # Loại tin
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="posts")   # Loại BĐS
    created_at = models.DateTimeField(auto_now_add=True)   # Ngày tạo
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")  # Người đăng bài 
    updated_at = models.DateTimeField(auto_now=True)       # Ngày cập nhật
    is_deleted = models.BooleanField(default=False)  # Soft delete
    approval_status = models.ForeignKey(
        'ApprovalStatus',
        on_delete=models.SET_NULL,
        null=True,
        related_name='posts'
    )
    post_status = models.ForeignKey(
        'PostStatus',
        on_delete=models.SET_NULL,
        null=True,
        related_name='posts'
    )

def save(self, *args, **kwargs):
    is_creating = self._state.adding  # True nếu là insert lần đầu

    # Set mặc định các trạng thái
    if not self.approval_status:
        self.approval_status = ApprovalStatus.objects.filter(name="Pending").first()
    if not self.post_status:
        self.post_status = PostStatus.objects.filter(name="Hidden").first()

    # Gán id nếu chưa có
    if not self.id:
        self.id = generate_unique_id(Post)

    # Nếu là tạo mới: lưu luôn, KHÔNG tạo PostHistory
    if is_creating:
        super().save(*args, **kwargs)
        return

    # Nếu là cập nhật: so sánh với bản cũ
    try:
        old = Post.objects.get(pk=self.pk)
    except Post.DoesNotExist:
        # Trường hợp hiếm khi DB chưa có vì lý do khác -> cứ lưu như tạo mới
        super().save(*args, **kwargs)
        return

    changed = False
    fields_to_track = [
        'title', 'description', 'address', 'location', 'details',
        'other_info', 'area', 'price', 'approval_status', 'post_status'
    ]
    old_content = {}
    new_content = {}
    for field in fields_to_track:
        old_val = getattr(old, field)
        new_val = getattr(self, field)
        if old_val != new_val:
            changed = True
            old_content[field] = old_val
            new_content[field] = new_val

    # Lưu thay đổi
    super().save(*args, **kwargs)

    # Ghi lịch sử nếu có thay đổi
    if changed:
        PostHistory.objects.create(
            post=self,
            user=self.user,
            old_content=str(old_content),
            new_content=str(new_content),
            change_type='update'
        )

    def save(self, *args, **kwargs):
        if not self.approval_status:
            self.approval_status = ApprovalStatus.objects.filter(name="Pending").first()
        if not self.post_status:
            self.post_status = PostStatus.objects.filter(name="Hidden").first()
        if not self.id:
            self.id = generate_unique_id(Post)
        # Kiểm tra thay đổi để tạo PostHistory
        if self.pk:
            old = Post.objects.get(pk=self.pk)
            changed = False
            fields_to_track = ['title', 'description', 'address', 'location', 'details', 'other_info', 'area', 'price', 'approval_status', 'post_status']
            old_content = {}
            new_content = {}
            for field in fields_to_track:
                old_val = getattr(old, field)
                new_val = getattr(self, field)
                if old_val != new_val:
                    changed = True
                    old_content[field] = old_val
                    new_content[field] = new_val
            if changed:
                PostHistory.objects.create(
                    post=self,
                    user=self.user,
                    old_content=str(old_content),
                    new_content=str(new_content),
                    change_type='update'
                )
        super().save(*args, **kwargs)   
    # def soft_delete(self, user=None):
    #     """Soft delete bài đăng"""
    #     if not self.is_deleted:
    #         old_content = {
    #             'title': self.title,
    #             'description': self.description,
    #             'address': self.address,
    #             'location': self.location,
    #             'details': self.details,
    #             'other_info': self.other_info,
    #             'area': self.area,
    #             'price': self.price,
    #             'approval_status': str(self.approval_status),
    #             'post_status': str(self.post_status)
    #         }
    #         self.is_deleted = True
    #         self.save()
    #         # Tạo PostHistory record
    #         PostHistory.objects.create(
    #             post=self,
    #             user=user or self.user,
    #             old_content=str(old_content),
    #             new_content=None,
    #             change_type='delete'
    #         )

    # def __str__(self): 
    #     return f"{self.title} ({self.post_type} - {self.category})"

# from django.db import models
# from django.core.validators import MinValueValidator
# from .User import User
# from .PostType import PostType
# from .Category import Category
# from .ApprovalStatus import ApprovalStatus
# from .PostStatus import PostStatus
# from .PostHistory import PostHistory

# import string, random

# # Hàm tạo ID ngẫu nhiên và đảm bảo tính duy nhất
# def generate_unique_id(model, field_name='id', length=9):
#     chars = string.ascii_uppercase + string.digits
#     for _ in range(100):
#         rid = ''.join(random.choices(chars, k=length))
#         if not model.objects.filter(**{field_name: rid}).exists():
#             return rid
#     raise RuntimeError("Không tạo được id duy nhất sau 100 lần thử")

# class Post(models.Model):
#     id = models.CharField(primary_key=True, max_length=9, editable=False)  # PK
#     title = models.CharField(max_length=255)
#     description = models.TextField()
#     address = models.JSONField()            # dict
#     location = models.JSONField()           # dict
#     details = models.JSONField()            # dict
#     other_info = models.JSONField(blank=True, null=True)
#     area = models.FloatField(validators=[MinValueValidator(0.01)])
#     price = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
#     post_type = models.ForeignKey(PostType, on_delete=models.CASCADE, related_name="posts")
#     category  = models.ForeignKey(Category,  on_delete=models.CASCADE, related_name="posts")
#     created_at = models.DateTimeField(auto_now_add=True)
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
#     updated_at = models.DateTimeField(auto_now=True)
#     is_deleted = models.BooleanField(default=False)
#     approval_status = models.ForeignKey('ApprovalStatus', on_delete=models.SET_NULL, null=True, related_name='posts')
#     post_status     = models.ForeignKey('PostStatus',     on_delete=models.SET_NULL, null=True, related_name='posts')

#     def save(self, *args, **kwargs):
#         creating = self._state.adding  # True nếu INSERT lần đầu

#         # GÁN PK ngay từ đầu khi tạo mới
#         if creating and not self.id:
#             self.id = generate_unique_id(type(self))

#         # Mặc định các trạng thái
#         if not self.approval_status:
#             self.approval_status = ApprovalStatus.objects.filter(name="Pending").first()
#         if not self.post_status:
#             self.post_status = PostStatus.objects.filter(name="Hidden").first()

#         if creating:
#             # Tạo mới: lưu, KHÔNG ghi PostHistory
#             return super().save(*args, **kwargs)

#         # Cập nhật: so sánh để ghi lịch sử
#         try:
#             old = type(self).objects.get(pk=self.pk)
#         except type(self).DoesNotExist:
#             return super().save(*args, **kwargs)

#         changed = False
#         fields = ['title','description','address','location','details','other_info','area','price','approval_status','post_status']
#         old_content, new_content = {}, {}
#         for f in fields:
#             ov, nv = getattr(old, f), getattr(self, f)
#             if ov != nv:
#                 changed = True
#                 old_content[f] = ov
#                 new_content[f] = nv

#         super().save(*args, **kwargs)

#         if changed:
#             PostHistory.objects.create(
#                 post=self, user=self.user,
#                 old_content=str(old_content), new_content=str(new_content),
#                 change_type='update'
#             )

#     def soft_delete(self, user=None):
#         if not self.is_deleted:
#             old_content = {
#                 'title': self.title,
#                 'description': self.description,
#                 'address': self.address,
#                 'location': self.location,
#                 'details': self.details,
#                 'other_info': self.other_info,
#                 'area': self.area,
#                 'price': self.price,
#                 'approval_status': str(self.approval_status),
#                 'post_status': str(self.post_status),
#             }
#             self.is_deleted = True
#             super().save()  # gọi trực tiếp super để tránh ghi history update
#             PostHistory.objects.create(
#                 post=self, user=user or self.user,
#                 old_content=str(old_content), new_content=None,
#                 change_type='delete'
#             )

#     def __str__(self):
#         return f"{self.title} ({self.post_type} - {self.category})"
