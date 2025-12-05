# engagement/services/rating_procs.py
from django.db import connection
from .db_utils import dictfetchall


def sp_eng_rating_upsert(user_id: str, post_id: str, score: int, comment: str = None):
    """
    Tạo/cập nhật rating cho (user_id, post_id).
    Trả về 1 dict: rating sau khi upsert.
    """
    with connection.cursor() as cursor:
        cursor.callproc(
            "sp_eng_rating_upsert",
            [user_id, post_id, score, comment],
        )
        rows = dictfetchall(cursor)
    return rows[0] if rows else None


def sp_eng_ratings_by_post(post_id: str):
    """
    Danh sách rating của 1 bài.
    """
    with connection.cursor() as cursor:
        cursor.callproc("sp_eng_ratings_by_post", [post_id])
        return dictfetchall(cursor)
