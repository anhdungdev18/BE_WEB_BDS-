# listings/services/auth_helpers.py
from accounts.services.authz import is_admin_like, user_has_perm


def get_actor_id(user) -> str:
    """
    ID dùng cho p_actor_id / user_id trong DB.
    Sửa lại nếu custom User của huynh không dùng pk = CHAR(9).
    """
    return str(user.id)
    # Nếu huynh có field riêng:
    # return user.user_id


def get_is_admin_flag(user) -> int:
    """
    Chuyển is_admin_like -> 0/1 để truyền vào stored procedure.
    """
    return 1 if is_admin_like(user) else 0


__all__ = ["get_actor_id", "get_is_admin_flag", "user_has_perm"]
