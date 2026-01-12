# accounts/serializers.py

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from accounts.models import MembershipOrder
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from accounts.models.role import Role
from accounts.models.permission import Permission

User = get_user_model()


def _get_avatar_link(obj):
    """
    Trả về link ảnh đại diện an toàn:
    - Nếu có file (ImageField + storage) => ưu tiên obj.anh_dai_dien.url
    - Nếu trường đang lưu sẵn URL dạng string => fallback str(obj.anh_dai_dien)
    - Không có => None
    """
    v = getattr(obj, "anh_dai_dien", None)
    if not v:
        return None
    # Ưu tiên url của storage (Cloudinary)
    try:
        return v.url
    except Exception:
        # Fallback: nếu DB lưu thẳng URL/string
        try:
            s = str(v)
            return s if s else None
        except Exception:
            return None


class BdsTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT: ngoài thông tin mặc định, thêm:
    - roles: ["MEMBER", "AGENT", ...]
    - perms: ["post.create", "post.create_vip", ...]
    - is_agent: bool
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        roles_qs = user.roles.all()
        role_names = list(roles_qs.values_list("role_name", flat=True))

        perm_codes = list(
            Permission.objects.filter(roles__in=roles_qs)
            .values_list("code", flat=True)
            .distinct()
        )

        token["roles"] = role_names
        token["perms"] = perm_codes
        token["is_agent"] = "AGENT" in role_names

        return token


# -------------------------------------------------------------------
# SERIALIZER CƠ BẢN CHO USER (TƯƠNG THÍCH CODE CŨ)
# -------------------------------------------------------------------

class UserSerializer(serializers.ModelSerializer):
    """
    Dùng cho auth_views cũ (trả thông tin user sau khi đăng ký/đăng nhập).
    """
    anh_dai_dien = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "anh_dai_dien"]

    def get_anh_dai_dien(self, obj):
        return _get_avatar_link(obj)


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    confirm_password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username đã tồn tại.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email đã được sử dụng.")
        return value

    def validate(self, attrs):
        password = attrs.get("password")
        confirm_password = attrs.get("confirm_password")

        if password != confirm_password:
            raise serializers.ValidationError({"confirm_password": _("Mật khẩu xác nhận không khớp.")})

        try:
            validate_password(password)
        except Exception as e:
            raise serializers.ValidationError({"password": list(e.messages)})

        return attrs

    def create(self, validated_data):
        username = validated_data.get("username")
        email = validated_data.get("email")
        password = validated_data.get("password")
        validated_data.pop("confirm_password", None)

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
        )
        return user


# -------------------------------------------------------------------
# USER BRIEF / DETAIL (CHO CÁC API MỚI)
# -------------------------------------------------------------------

class UserBriefSerializer(serializers.ModelSerializer):
    """
    Dùng cho list user, hoặc embed trong các object khác.
    """
    anh_dai_dien = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "anh_dai_dien"]

    def get_anh_dai_dien(self, obj):
        return _get_avatar_link(obj)


class UserDetailSerializer(serializers.ModelSerializer):
    """
    Dùng cho trang Hồ sơ hoặc admin xem chi tiết 1 user.
    """
    anh_dai_dien = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "is_active",
            "so_dien_thoai",
            "address",
            "bio",
            "anh_dai_dien",
        ]
        read_only_fields = ["id", "email", "is_active"]

    def get_anh_dai_dien(self, obj):
        return _get_avatar_link(obj)


# -------------------------------------------------------------------
# PROFILE / HỒ SƠ
# -------------------------------------------------------------------

class ProfileUpdateSerializer(serializers.Serializer):
    username = serializers.CharField(required=False, allow_blank=True, max_length=150)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=30)
    address = serializers.CharField(required=False, allow_blank=True, max_length=255)
    bio = serializers.CharField(required=False, allow_blank=True, style={"base_template": "textarea.html"})
    avatar = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="URL ảnh đại diện (Cloudinary/S3, ...)",
    )


class AdminUpdateUserProfileSerializer(ProfileUpdateSerializer):
    pass


# -------------------------------------------------------------------
# PASSWORD
# -------------------------------------------------------------------

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, style={"input_type": "password"})
    new_password = serializers.CharField(write_only=True, style={"input_type": "password"})
    confirm_password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs):
        new_password = attrs.get("new_password")
        confirm_password = attrs.get("confirm_password")

        if new_password != confirm_password:
            raise serializers.ValidationError({"confirm_password": _("Mật khẩu xác nhận không khớp.")})

        user = self.context.get("user")
        try:
            validate_password(new_password, user=user)
        except Exception as e:
            raise serializers.ValidationError({"new_password": list(e.messages)})

        return attrs


class AdminResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, style={"input_type": "password"})
    confirm_password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs):
        new_password = attrs.get("new_password")
        confirm_password = attrs.get("confirm_password")

        if new_password != confirm_password:
            raise serializers.ValidationError({"confirm_password": _("Mật khẩu xác nhận không khớp.")})

        user = self.context.get("target_user")
        try:
            validate_password(new_password, user=user)
        except Exception as e:
            raise serializers.ValidationError({"new_password": list(e.messages)})

        return attrs


# -------------------------------------------------------------------
# FILTER / LIST USER (CHO ADMIN)
# -------------------------------------------------------------------

class UserListFilterSerializer(serializers.Serializer):
    q = serializers.CharField(required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False, default=True)
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=100, default=20)


# -------------------------------------------------------------------
# MEMBERSHIP (GIỮ NGUYÊN)
# -------------------------------------------------------------------

class MembershipOrderListSerializer(serializers.ModelSerializer):
    user_email = serializers.SerializerMethodField()
    user_username = serializers.SerializerMethodField()
    plan_code = serializers.CharField(source="plan.code")
    plan_name = serializers.CharField(source="plan.name")

    class Meta:
        model = MembershipOrder
        fields = [
            "id",
            "status",
            "amount_vnd",
            "transfer_note",
            "qr_image_url",
            "created_at",
            "paid_at",
            "user_id",
            "user_email",
            "user_username",
            "plan_code",
            "plan_name",
        ]

    def get_user_email(self, obj):
        return getattr(obj.user, "email", None)

    def get_user_username(self, obj):
        return getattr(obj.user, "username", None)


class MeSerializer(serializers.ModelSerializer):
    """
    Giữ để tương thích chỗ nào đó đang dùng anh_dai_dien_url,
    đồng thời thêm luôn anh_dai_dien (cùng giá trị) để FE thống nhất.
    """
    anh_dai_dien = serializers.SerializerMethodField()
    anh_dai_dien_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "anh_dai_dien", "anh_dai_dien_url"]

    def get_anh_dai_dien(self, obj):
        return _get_avatar_link(obj)

    def get_anh_dai_dien_url(self, obj):
        return _get_avatar_link(obj)
