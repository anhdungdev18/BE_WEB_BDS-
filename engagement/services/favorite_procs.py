# engagement/services/favorite_procs.py
from django.db import connection
from .db_utils import dictfetchall


def sp_eng_favorite_toggle(user_id: str, post_id: str) -> dict:
    """
    Gọi SP sp_eng_favorite_toggle
    Trả về: {"favorited": 0/1}
    """
    with connection.cursor() as cursor:
        cursor.callproc("sp_eng_favorite_toggle", [user_id, post_id])
        rows = dictfetchall(cursor)
    return rows[0] if rows else {"favorited": 0}


def sp_eng_favorites_by_user(user_id: str):
    """
    List bài user đã thích.
    """
    with connection.cursor() as cursor:
        cursor.callproc("sp_eng_favorites_by_user", [user_id])
        return dictfetchall(cursor)


def sp_eng_favorites_by_post(post_id: str):
    """
    List user đã thích 1 bài.
    """
    with connection.cursor() as cursor:
        cursor.callproc("sp_eng_favorites_by_post", [post_id])
        return dictfetchall(cursor)
