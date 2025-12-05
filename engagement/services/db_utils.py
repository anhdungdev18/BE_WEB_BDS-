# engagement/services/db_utils.py
from django.db import connection


def dictfetchall(cursor):
    """
    Trả về list[dict] từ cursor.
    """
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]
