# engagement/views/comment_api.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from engagement.services.comment_procs import (
    sp_eng_comment_create,
    sp_eng_comments_by_post,
)


class CommentCreateAPIView(APIView):
    """
    POST /api/engagement/comments/
        body: { "post_id": "...", "content": "...", "parent_id": null }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        post_id = request.data.get("post_id")
        content = request.data.get("content")
        parent_id = request.data.get("parent_id")

        if not post_id:
            return Response(
                {"detail": "post_id là bắt buộc"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not content:
            return Response(
                {"detail": "content không được rỗng"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            parent_id = int(parent_id) if parent_id is not None else None
        except (TypeError, ValueError):
            parent_id = None

        user_id = str(request.user.id)
        row = sp_eng_comment_create(
            user_id=user_id,
            post_id=post_id,
            content=content,
            parent_id=parent_id,
        )
        return Response(row, status=status.HTTP_201_CREATED)


class CommentListByPostAPIView(APIView):
    """
    GET /api/engagement/comments/list/?post_id=
        -> danh sách comment đã APPROVED
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        post_id = request.query_params.get("post_id")
        if not post_id:
            return Response(
                {"detail": "Thiếu post_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        items = sp_eng_comments_by_post(post_id=post_id, status="APPROVED")
        return Response(items, status=status.HTTP_200_OK)


class CommentUsersByPostAPIView(APIView):
    """
    GET /api/engagement/comments/users/?post_id=
        -> Dùng khi FE chỉ cần user_id + content để tự join accounts
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        post_id = request.query_params.get("post_id")
        if not post_id:
            return Response(
                {"detail": "Thiếu post_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        items = sp_eng_comments_by_post(post_id=post_id, status="APPROVED")
        # items đã là list dict với user_id, content, created_at,...
        return Response(
            {"post_id": post_id, "comments": items},
            status=status.HTTP_200_OK,
        )
