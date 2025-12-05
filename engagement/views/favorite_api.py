# engagement/views/favorite_api.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from engagement.services.favorite_procs import (
    sp_eng_favorite_toggle,
    sp_eng_favorites_by_user,
    sp_eng_favorites_by_post,
)


class FavoriteToggleAPIView(APIView):
    """
    POST /api/engagement/favorites/toggle/
        body: { "post_id": "P0000001" }

    -> Gọi SP toggle, trả {"favorited": 1/0}
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        post_id = request.data.get("post_id")
        if not post_id:
            return Response(
                {"detail": "post_id là bắt buộc"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_id = str(request.user.id)
        result = sp_eng_favorite_toggle(user_id=user_id, post_id=post_id)
        return Response(result, status=status.HTTP_200_OK)


class FavoriteMyListAPIView(APIView):
    """
    GET /api/engagement/favorites/my/
        -> ds bài mình đã yêu thích
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user_id = str(request.user.id)
        items = sp_eng_favorites_by_user(user_id=user_id)
        return Response(items, status=status.HTTP_200_OK)


class FavoriteUsersByPostAPIView(APIView):
    """
    GET /api/engagement/favorites/users/?post_id=
        -> ds user_id đã thích bài này
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        post_id = request.query_params.get("post_id")
        if not post_id:
            return Response(
                {"detail": "Thiếu post_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        items = sp_eng_favorites_by_post(post_id=post_id)
        # items: [{id,user_id,post_id,created_at},...]
        # FE có thể extract user_id để call accounts batch
        return Response(
            {
                "post_id": post_id,
                "favorites": items,
            },
            status=status.HTTP_200_OK,
        )
