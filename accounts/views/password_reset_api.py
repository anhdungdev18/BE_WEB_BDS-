from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from django.core.exceptions import ValidationError

from accounts.services.password_reset_service import (
    create_password_reset_token_for_email,
    reset_password_with_token,
)


class PasswordForgotAPIView(APIView):
    """
    POST /api/accounts/password/forgot/
    body: { "email": "..." }
    -> luôn trả ok (không lộ email tồn tại hay không)
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        email = request.data.get("email", "").strip()
        if not email:
            return Response({"detail": "Thiếu email"}, status=status.HTTP_400_BAD_REQUEST)

        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        ip_address = xff.split(",")[0].strip() if xff else request.META.get("REMOTE_ADDR")
        user_agent = request.META.get("HTTP_USER_AGENT", "")[:255]

        create_password_reset_token_for_email(
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            expiry_minutes=30,
        )

        return Response(
            {"ok": True, "detail": "Nếu email tồn tại, link đặt lại mật khẩu đã được gửi."},
            status=status.HTTP_200_OK,
        )


class PasswordResetAPIView(APIView):
    """
    POST /api/accounts/password/reset/
    body: { "token": "...", "new_password": "..." }
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        token = request.data.get("token", "").strip()
        new_password = request.data.get("new_password", "")

        if not token or not new_password:
            return Response(
                {"detail": "Thiếu token hoặc new_password"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            reset_password_with_token(token, new_password)
            return Response({"ok": True}, status=status.HTTP_200_OK)
        except ValidationError as ve:
            # password yếu theo validators
            return Response({"detail": ve.messages}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            code = str(e)
            if code == "TOKEN_INVALID_OR_EXPIRED":
                return Response({"detail": "Token không hợp lệ hoặc đã hết hạn"}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"detail": "Không thể đặt lại mật khẩu"}, status=status.HTTP_400_BAD_REQUEST)
