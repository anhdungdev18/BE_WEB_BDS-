from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from rest_framework_simplejwt.tokens import RefreshToken

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

User = get_user_model()


class GoogleLoginAPIView(APIView):
    """
    POST /api/accounts/google-login/
    body: { "id_token": "<id_token_google_tra_ve>" }

    - Verify id_token với Google
    - Nếu hợp lệ: tạo/tìm User theo email (auto đăng ký nếu chưa có)
    - Trả về access/refresh JWT
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        token = request.data.get("id_token")
        if not token:
            return Response(
                {"detail": "Thiếu id_token"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 1) Verify token với Google
        try:
            idinfo = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID,
            )
        except ValueError:
            return Response(
                {"detail": "id_token không hợp lệ"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 2) Lấy thông tin từ token
        email      = idinfo.get("email")
        full_name  = idinfo.get("name") or ""
        picture    = idinfo.get("picture")  # avatar Google
        google_sub = idinfo.get("sub")      # id duy nhất của tài khoản Google

        if not email:
            return Response(
                {"detail": "Không lấy được email từ Google"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 3) Tự generate username nếu cần (AbstractUser vẫn cần username)
        base_username = email.split("@")[0]
        username = base_username

        # Tránh trùng username (phòng khi đã có user khác tên giống vậy)
        idx = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{idx}"
            idx += 1

        # 4) Tạo hoặc lấy user theo email
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                # AbstractUser fields
                "username": username,
                "first_name": full_name,   # hoặc tách họ/tên nếu muốn
                # Custom fields của model huynh:
                "anh_dai_dien": picture,
                "da_xac_minh": True,
            },
        )

        # Nếu user đã tồn tại nhưng chưa xác minh, có thể cập nhật thêm:
        if not created:
            updated = False
            if not user.da_xac_minh:
                user.da_xac_minh = True
                updated = True
            if picture and not user.anh_dai_dien:
                user.anh_dai_dien = picture
                updated = True
            if updated:
                user.save(update_fields=["da_xac_minh", "anh_dai_dien"])

        if not user.is_active:
            return Response(
                {"detail": "Tài khoản đã bị khóa, vui lòng liên hệ quản trị viên."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # 5) Tạo JWT token
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        return Response(
            {
                "access": str(access),
                "refresh": str(refresh),
                "user": {
                    "id": user.id,                # chuỗi 9 ký tự của huynh
                    "email": user.email,
                    "username": user.username,
                    "anh_dai_dien": user.anh_dai_dien,
                    "da_xac_minh": user.da_xac_minh,
                },
                "is_new_user": created,
            },
            status=status.HTTP_200_OK,
        )
