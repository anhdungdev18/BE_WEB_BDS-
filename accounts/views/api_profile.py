# accounts/views/api_profile.py

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


class MeProfileAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = ProfileUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # chỉ user tự update mình
        result = user_sp.update_own_profile(request.user, serializer.validated_data)
        return Response(result, status=status.HTTP_200_OK)


class ChangePasswordAPIView(APIView):
    """
    POST /api/accounts/password/change
    Body:
      - old_password
      - new_password
      - confirm_password
    """
    permission_classes = [permissions.IsAuthenticated]   # ✅ Bắt buộc phải đăng nhập

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

        return Response(result, status=status.HTTP_200_OK)
