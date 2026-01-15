# accounts/views/api_public_profile.py

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status

User = get_user_model()


def _avatar_url(user):
    v = getattr(user, "anh_dai_dien", None)
    if not v:
        return None
    try:
        return v.url
    except Exception:
        # fallback nếu trường lưu dạng string/url
        try:
            s = str(v)
            return s if s else None
        except Exception:
            return None


class PublicUserProfileAPIView(APIView):
    """
    GET /api/accounts/users/<user_id>/public-profile/
      -> Thông tin công khai của 1 user (cho người khác xem, không cần login)
    """
    permission_classes = [AllowAny]

    def get(self, request, user_id: str):
        user = get_object_or_404(User, pk=user_id)

        data = {
            "id": user.id,
            "full_name": getattr(user, "full_name", None),
            "first_name": getattr(user, "first_name", None),
            "last_name": getattr(user, "last_name", None),
            "anh_dai_dien": _avatar_url(user),
            "bio": getattr(user, "bio", None),
            "email": getattr(user, "email", None),
            "phone": getattr(user, "so_dien_thoai", None) or getattr(user, "phone", None),
            "joined_at": user.date_joined,
        }
        return Response(data, status=status.HTTP_200_OK)
