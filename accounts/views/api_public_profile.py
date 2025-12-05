# accounts/views/api_public_profile.py

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status

User = get_user_model()


class PublicUserProfileAPIView(APIView):
    """
    GET /api/accounts/users/<user_id>/public-profile/
      -> Thông tin công khai của 1 user (cho người khác xem, không cần login)
    """
    permission_classes = [AllowAny]

    def get(self, request, user_id: str):
        # lấy user theo id (CHAR(9) mà huynh đang dùng)
        user = get_object_or_404(User, pk=user_id)

        data = {
            "id": user.id,
            "username": user.username,
            "full_name": getattr(user, "full_name", None),
            "avatar": getattr(user, "anh_dai_dien", None),
            "bio": getattr(user, "bio", None),
            "joined_at": user.date_joined,
        }
        return Response(data, status=status.HTTP_200_OK)
