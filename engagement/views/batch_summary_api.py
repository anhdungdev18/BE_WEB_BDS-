from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db import connection
from engagement.services.db_utils import dictfetchall


class PostSummaryBatchAPIView(APIView):
    """
    POST /api/engagement/posts/summary/batch/
    Body: { "post_ids": ["P0000001","P0000002",...] }

    - AllowAny
    - Nếu user login -> trả thêm "favorited" cho user đó
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        post_ids = request.data.get("post_ids") or []
        if not isinstance(post_ids, list) or not post_ids:
            return Response(
                {"detail": "post_ids phải là list và không rỗng"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # chống spam
        post_ids = [str(x).strip() for x in post_ids if str(x).strip()]
        post_ids = post_ids[:100]

        user_id = str(request.user.id) if request.user.is_authenticated else None

        # Gọi SP batch (khuyên dùng cho MySQL)
        with connection.cursor() as cursor:
            cursor.callproc("sp_eng_post_summary_batch", [",".join(post_ids), user_id])
            rows = dictfetchall(cursor)

        # rows: [{post_id, view_count, rating_avg, rating_count, comment_count, favorited}, ...]
        return Response({"items": rows}, status=status.HTTP_200_OK)
