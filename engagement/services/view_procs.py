# engagement/services/view_procs.py
from django.db import connection
from .db_utils import dictfetchall


def sp_eng_post_view_add(
    user_id: str,
    post_id: str,
    session_id: str = None,
    ip_address: str = None,
    user_agent: str = None,
):
    """
    Ghi nhận 1 lượt xem, trả về {"id": ...} hoặc None.
    """
    with connection.cursor() as cursor:
        cursor.callproc(
            "sp_eng_post_view_add",
            [user_id, post_id, session_id, ip_address, user_agent],
        )
        rows = dictfetchall(cursor)
    return rows[0] if rows else None


def sp_eng_post_view_summary(post_id: str):
    """
    Lấy tổng lượt xem 1 bài.
    Trả về: {"post_id": ..., "view_count": ...} hoặc None.
    """
    with connection.cursor() as cursor:
        cursor.callproc("sp_eng_post_view_summary", [post_id])
        rows = dictfetchall(cursor)
    return rows[0] if rows else {"post_id": post_id, "view_count": 0}
