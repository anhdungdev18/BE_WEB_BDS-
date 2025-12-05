import string
import random
from django.db import models
from django.contrib.auth.models import AbstractUser, PermissionsMixin, AbstractBaseUser, BaseUserManager
from django.contrib.auth.hashers import make_password, check_password
from .Role import Role
from ..managers import CustomUserManager

# --- Hàm tạo ID ngẫu nhiên và duy nhất ---
def generate_unique_id(model, field_name='id', length=9):
    chars = string.ascii_uppercase + string.digits  # A-Z + 0-9
    while True:
        new_id = ''.join(random.choices(chars, k=length))
        if not model.objects.filter(**{field_name: new_id}).exists():
            return new_id


class User(AbstractUser):
    id = models.CharField(primary_key=True, max_length=9, editable=False)
    # Giữ nguyên trường username của AbstractUser!
    email = models.EmailField(
        max_length=255,
        unique=True,
        error_messages={
            'unique': "Email này đã được sử dụng.",
        }
    )
    # ho_ten = models.CharField(max_length=200)
    cccd_number = models.CharField(max_length=12, blank=True, null=True)
    so_dien_thoai = models.CharField(max_length=30, blank=True, null=True)
    anh_dai_dien = models.TextField(blank=True, null=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    da_xac_minh = models.BooleanField(default=False)
    ngay_tao = models.DateTimeField(auto_now_add=True)
    ngay_cap_nhat = models.DateTimeField(auto_now=True)
    bio = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    roles = models.ManyToManyField(
        Role,
        through='UserRole',
        through_fields=('user', 'role'),
        related_name='users'
    )

    def __str__(self):
        return self.email or self.username

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = generate_unique_id(User)
        super().save(*args, **kwargs)
