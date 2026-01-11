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
class FavoriteMeAPIView(APIView):
    """
    GET /api/engagement/favorites/me/?post_id=
        -> {post_id, favorited: 1/0}
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        post_id = request.query_params.get("post_id")
        if not post_id:
            return Response({"detail": "Thiếu post_id"}, status=status.HTTP_400_BAD_REQUEST)

        user_id = str(request.user.id)

        rows = sp_eng_favorites_by_user(user_id=user_id)
        favorited = 0
        for r in rows:
            if str(r.get("post_id")) == str(post_id):
                favorited = 1
                break

        return Response({"post_id": post_id, "favorited": favorited}, status=status.HTTP_200_OK)


class FavoriteMyBatchAPIView(APIView):
    """
    GET /api/engagement/favorites/my/batch/?post_ids=P1,P2,P3
        -> {"P1":1,"P2":0,"P3":1}
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        raw = request.query_params.get("post_ids", "")
        post_ids = [p.strip() for p in raw.split(",") if p.strip()]
        if not post_ids:
            return Response({"detail": "Thiếu post_ids"}, status=status.HTTP_400_BAD_REQUEST)

        if len(post_ids) > 200:
            return Response({"detail": "post_ids quá nhiều (tối đa 200)"}, status=status.HTTP_400_BAD_REQUEST)

        user_id = str(request.user.id)
        rows = sp_eng_favorites_by_user(user_id=user_id)

        fav_set = {str(r.get("post_id")) for r in rows if r.get("post_id")}
        result = {pid: (1 if str(pid) in fav_set else 0) for pid in post_ids}

        return Response(result, status=status.HTTP_200_OK)