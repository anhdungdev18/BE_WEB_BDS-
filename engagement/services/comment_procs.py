# engagement/services/comment_procs.py
from django.db import connection
from .db_utils import dictfetchall


def sp_eng_comment_create(
    user_id: str,
    post_id: str,
    content: str,
    parent_id: int = None,
):
    """
    Tạo comment mới, trả về bản ghi vừa tạo.
    """
    with connection.cursor() as cursor:
        cursor.callproc(
            "sp_eng_comment_create",
            [user_id, post_id, content, parent_id],
        )
        rows = dictfetchall(cursor)
    return rows[0] if rows else None


def sp_eng_comments_by_post(post_id: str, status: str = "APPROVED"):
    """
    Danh sách comment của 1 bài theo status (thường là APPROVED).
    """
    with connection.cursor() as cursor:
        cursor.callproc("sp_eng_comments_by_post", [post_id, status])
        return dictfetchall(cursor)
