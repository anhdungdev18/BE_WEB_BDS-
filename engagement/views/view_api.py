# engagement/views/view_api.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from engagement.services.view_procs import (
    sp_eng_post_view_add,
    sp_eng_post_view_summary,
)


class PostViewCreateAPIView(APIView):
    """
    POST /api/engagement/views/
        body: { "post_id": "...", "session_id": "abc" }
        -> ghi nhận 1 lượt xem (guest hoặc user)
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        post_id = request.data.get("post_id")
        session_id = request.data.get("session_id")

        if not post_id:
            return Response(
                {"detail": "post_id là bắt buộc"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user if request.user.is_authenticated else None
        user_id = str(user.id) if user else None

        ip_address = request.META.get("REMOTE_ADDR")
        user_agent = request.META.get("HTTP_USER_AGENT", "")[:255]

        sp_eng_post_view_add(
            user_id=user_id,
            post_id=post_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return Response({"ok": True}, status=status.HTTP_201_CREATED)


class PostViewSummaryAPIView(APIView):
    """
    GET /api/engagement/views/summary/?post_id=
        -> trả {post_id, view_count}
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        post_id = request.query_params.get("post_id")
        if not post_id:
            return Response(
                {"detail": "Thiếu post_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        summary = sp_eng_post_view_summary(post_id=post_id)
        return Response(summary, status=status.HTTP_200_OK)
