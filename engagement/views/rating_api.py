# engagement/views/rating_api.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from engagement.services.rating_procs import (
    sp_eng_rating_upsert,
    sp_eng_ratings_by_post,
)
from django.contrib.auth import get_user_model

User = get_user_model()


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
        user_ids = {str(r.get("user_id")) for r in items if r.get("user_id")}
        if user_ids:
            users = User.objects.filter(id__in=list(user_ids)).values("id", "username", "email")
            user_map = {str(u["id"]): u for u in users}
            for r in items:
                uid = str(r.get("user_id"))
                u = user_map.get(uid)
                if u:
                    r["user_name"] = u.get("username") or u.get("email") or ""
                else:
                    r["user_name"] = ""
        return Response(items, status=status.HTTP_200_OK)
class RatingSummaryAPIView(APIView):
    """
    GET /api/engagement/ratings/summary/?post_id=
        -> {post_id, avg_score, rating_count, breakdown}
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        post_id = request.query_params.get("post_id")
        if not post_id:
            return Response({"detail": "Thiếu post_id"}, status=status.HTTP_400_BAD_REQUEST)

        items = sp_eng_ratings_by_post(post_id=post_id)  # score đã là "score" theo SP của huynh
        breakdown = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}

        scores = []
        for r in items:
            try:
                s = int(r.get("score"))
                if 1 <= s <= 5:
                    scores.append(s)
                    breakdown[str(s)] += 1
            except Exception:
                pass

        rating_count = len(scores)
        avg_score = round(sum(scores) / rating_count, 2) if rating_count else 0

        return Response(
            {
                "post_id": post_id,
                "avg_score": avg_score,
                "rating_count": rating_count,
                "breakdown": breakdown,
            },
            status=status.HTTP_200_OK,
        )
