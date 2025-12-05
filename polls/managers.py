from django.contrib.auth.base_user import BaseUserManager

class CustomUserManager(BaseUserManager):
    """Quản lý tạo user và superuser."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Người dùng phải có địa chỉ email')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser phải có is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser phải có is_superuser=True.')

        return self.create_user(email, password, **extra_fields)
