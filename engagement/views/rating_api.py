# engagement/views/rating_api.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from engagement.services.rating_procs import (
    sp_eng_rating_upsert,
    sp_eng_ratings_by_post,
)


class RatingUpsertAPIView(APIView):
    """
    POST /api/engagement/ratings/
        body: { "post_id": "...", "score": 5, "comment": "..." }

    -> 1 user chỉ có 1 rating / bài. Gọi SP upsert.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        post_id = request.data.get("post_id")
        score = request.data.get("score")
        comment = request.data.get("comment")

        if not post_id:
            return Response(
                {"detail": "post_id là bắt buộc"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            score = int(score)
        except (TypeError, ValueError):
            return Response(
                {"detail": "score phải là số nguyên 1–5"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if score < 1 or score > 5:
            return Response(
                {"detail": "score phải từ 1 đến 5"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_id = str(request.user.id)
        row = sp_eng_rating_upsert(
            user_id=user_id,
            post_id=post_id,
            score=score,
            comment=comment,
        )
        return Response(row, status=status.HTTP_200_OK)


class RatingListByPostAPIView(APIView):
    """
    GET /api/engagement/ratings/list/?post_id=
        -> danh sách rating của 1 bài
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        post_id = request.query_params.get("post_id")
        if not post_id:
            return Response(
                {"detail": "Thiếu post_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        items = sp_eng_ratings_by_post(post_id=post_id)
        return Response(items, status=status.HTTP_200_OK)
