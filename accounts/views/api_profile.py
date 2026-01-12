# accounts/views/api_profile.py

import json
from django.contrib.auth.hashers import check_password, make_password
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from accounts.services import user_sp
from accounts.serializers import (
    UserDetailSerializer,
    ProfileUpdateSerializer,
    ChangePasswordSerializer,
)


def _maybe_load_json(raw):
    """
    SP thường trả JSON string. Nếu raw là string JSON -> loads về dict.
    Nếu raw đã là dict/list -> giữ nguyên.
    """
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


class MeProfileAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Giữ logic hiện tại: dùng serializer
        data = dict(UserDetailSerializer(request.user).data)

        # Nếu serializer chưa có anh_dai_dien thì bơm thêm từ SP (đúng nguồn FE đang dùng)
        if "anh_dai_dien" not in data:
            raw = user_sp.get_user_json(str(request.user.id))
            sp_obj = _maybe_load_json(raw)
            if isinstance(sp_obj, dict) and "anh_dai_dien" in sp_obj:
                data["anh_dai_dien"] = sp_obj.get("anh_dai_dien")
            else:
                data["anh_dai_dien"] = None

        return Response(data, status=status.HTTP_200_OK)

    def put(self, request):
        serializer = ProfileUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # chỉ user tự update mình
        result = user_sp.update_own_profile(request.user, serializer.validated_data)

        # SP trả JSON string -> parse về dict để FE nhận object có anh_dai_dien
        return Response(_maybe_load_json(result), status=status.HTTP_200_OK)


class ChangePasswordAPIView(APIView):
    """
    POST /api/accounts/password/change
    Body:
      - old_password
      - new_password
      - confirm_password
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"user": request.user},
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        old_password = serializer.validated_data["old_password"]
        new_password = serializer.validated_data["new_password"]

        # ✅ Chỉ đổi nếu nhập đúng mật khẩu cũ
        if not check_password(old_password, request.user.password):
            return Response(
                {"old_password": ["Mật khẩu cũ không chính xác."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_hash = make_password(new_password)

        try:
            result = user_sp.change_own_password(request.user, new_hash)
        except PermissionError as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)

        return Response(_maybe_load_json(result), status=status.HTTP_200_OK)
