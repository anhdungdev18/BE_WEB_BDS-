# accounts/views/api_admin_users.py

import json
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from accounts.serializers import (
    UserListFilterSerializer,
    AdminUpdateUserProfileSerializer,
    AdminResetPasswordSerializer,
)
from accounts.services import user_sp
from accounts.services.authz import user_has_perm

User = get_user_model()


def _maybe_load_json(raw):
    """SP có thể trả JSON string; parse về dict/list nếu được."""
    if raw is None:
        return None
    if isinstance(raw, (dict, list)):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except Exception:
            return raw
    return raw


def _ensure_avatar_key(obj):
    """Đảm bảo dict user luôn có key anh_dai_dien (nếu thiếu)."""
    if isinstance(obj, dict) and "anh_dai_dien" not in obj:
        obj["anh_dai_dien"] = None
    return obj


class AdminUserListAPIView(APIView):
    """
    GET /api/accounts/users
      - q, is_active, page, page_size (query params)
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # ✅ Dùng đúng permission đã seed
        if not user_has_perm(request.user, "user.view"):
            return Response(
                {"detail": "NO_PERMISSION_VIEW_USERS"},
                status=status.HTTP_403_FORBIDDEN,
            )

        ser_filter = UserListFilterSerializer(data=request.query_params)
        ser_filter.is_valid(raise_exception=True)
        f = ser_filter.validated_data

        data = user_sp.list_users_json(
            actor=request.user,
            q=f.get("q"),
            is_active=f.get("is_active"),
            page=f.get("page", 1),
            page_size=f.get("page_size", 20),
        )

        # data có thể là list[dict] (chuẩn) hoặc lỡ có list[str JSON]
        results = []
        for item in data or []:
            parsed = _maybe_load_json(item)
            if isinstance(parsed, dict):
                results.append(_ensure_avatar_key(parsed))
            else:
                # fallback nếu item không parse được
                results.append(parsed)

        return Response(results, status=status.HTTP_200_OK)


class AdminUserDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, user_id: str):
        # ✅ CHỈ ADMIN / STAFF MỚI ĐƯỢC SỬA NGƯỜI KHÁC
        if not user_has_perm(request.user, "user.manage"):
            return Response(
                {"detail": "NO_PERMISSION_MANAGE_USER"},
                status=status.HTTP_403_FORBIDDEN,
            )

        target_user = get_object_or_404(User, pk=user_id)

        serializer = AdminUpdateUserProfileSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = user_sp.admin_update_user_profile(
                actor=request.user,
                target_user_id=target_user.id,
                data=serializer.validated_data,
            )
        except PermissionError as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)

        parsed = _maybe_load_json(result)
        if isinstance(parsed, dict):
            parsed = _ensure_avatar_key(parsed)

        return Response(parsed, status=status.HTTP_200_OK)


class AdminResetPasswordAPIView(APIView):
    """
    POST /api/accounts/admin/users/<user_id>/reset-password/
    Body:
      - new_password
      - confirm_password
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, user_id: str):
        if not user_has_perm(request.user, "user.reset_password"):
            return Response(
                {"detail": "NO_PERMISSION_RESET_PASSWORD"},
                status=status.HTTP_403_FORBIDDEN,
            )

        target_user = get_object_or_404(User, pk=user_id)

        serializer = AdminResetPasswordSerializer(
            data=request.data,
            context={"target_user": target_user},
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        new_password = serializer.validated_data["new_password"]
        new_hash = make_password(new_password)

        try:
            result = user_sp.admin_reset_user_password(
                actor=request.user,
                target_user_id=target_user.id,
                new_password_hash=new_hash,
            )
        except PermissionError as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)

        return Response(_maybe_load_json(result), status=status.HTTP_200_OK)


class AdminApproveUserAPIView(APIView):
    """
    POST /api/accounts/admin/users/<user_id>/approve/
    Body (optional):
      - is_active: true/false (default true)
      - verified: true/false (default true) -> maps to da_xac_minh
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, user_id: str):
        if not user_has_perm(request.user, "user.manage"):
            return Response(
                {"detail": "NO_PERMISSION_MANAGE_USER"},
                status=status.HTTP_403_FORBIDDEN,
            )

        target_user = get_object_or_404(User, pk=user_id)
        is_active = request.data.get("is_active", True)
        verified = request.data.get("verified", True)

        target_user.is_active = bool(is_active)
        target_user.da_xac_minh = bool(verified)
        target_user.save(update_fields=["is_active", "da_xac_minh"])

        return Response(
            {
                "id": target_user.id,
                "username": target_user.username,
                "email": target_user.email,
                "is_active": target_user.is_active,
                "da_xac_minh": target_user.da_xac_minh,
            },
            status=status.HTTP_200_OK,
        )
