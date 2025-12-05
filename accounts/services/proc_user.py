# accounts/services/proc_user.py

from typing import Optional, Any
from django.db import connection


def _fetch_one_json(cur) -> Optional[Any]:
    """
    SP user_* thường SELECT JSON_OBJECT(...) AS result
    -> lấy cột result của dòng đầu tiên.
    Huynh có thể chỉnh thêm json.loads(...) nếu cần dạng dict.
    """
    row = cur.fetchone()
    return None if not row else row[0]  # alias 'result'


def sp_user_get_json(user_id: str):
    """
    Gọi SP sp_user_get_json(user_id) -> trả JSON thông tin user.
    (SP này không đổi tham số)
    """
    with connection.cursor() as cur:
        cur.callproc("sp_user_get_json", [user_id])
        return _fetch_one_json(cur)


def sp_user_update_profile_raw(
    target_user_id: str,
    actor_id: str,
    is_admin: bool,
    username: Optional[str],
    phone: Optional[str],
    address: Optional[str],
    bio: Optional[str],
    avatar: Optional[str],
):
    """
    Wrapper cho SP sp_user_update_profile (bản mới):

      sp_user_update_profile(
        p_target_user_id,
        p_actor_id,
        p_is_admin,
        p_username,
        p_so_dien_thoai,
        p_address,
        p_bio,
        p_anh_dai_dien
      )
    """
    with connection.cursor() as cur:
        cur.callproc(
            "sp_user_update_profile",
            [
                target_user_id,
                actor_id,
                1 if is_admin else 0,
                username,
                phone,
                address,
                bio,
                avatar,
            ],
        )
        return _fetch_one_json(cur)


def sp_user_change_password_raw(
    target_user_id: str,
    actor_id: str,
    is_admin: bool,
    new_password_hash: str,
):
    """
    Wrapper cho SP sp_user_change_password (bản mới):

      sp_user_change_password(
        p_target_user_id,
        p_actor_id,
        p_is_admin,
        p_new_password_hash
      )
    """
    with connection.cursor() as cur:
        cur.callproc(
            "sp_user_change_password",
            [
                target_user_id,
                actor_id,
                1 if is_admin else 0,
                new_password_hash,
            ],
        )
        return _fetch_one_json(cur)


def sp_users_list_json(q=None, is_active=None, page: int = 1, page_size: int = 20):
    """
    Wrapper cho SP sp_users_list_json, trả list JSON.
    """
    with connection.cursor() as cur:
        cur.callproc("sp_users_list_json", [q, is_active, page, page_size])
        return [r[0] for r in cur.fetchall()]  # mỗi hàng là 1 JSON_OBJECT
# accounts/services/proc_user.py

# ... các hàm ở trên giữ nguyên ...


def sp_user_update_profile(
    user_id: str,
    username=None,
    phone=None,
    address=None,
    bio=None,
    avatar=None,
):
    """
    Wrapper tương thích code cũ:
    - Ngày xưa SP chỉ nhận user_id -> hiểu là user tự sửa hồ sơ mình.
    - Bây giờ gọi xuống sp_user_update_profile_raw với:
        target_user_id = user_id
        actor_id       = user_id
        is_admin       = False (user thường)
    """
    return sp_user_update_profile_raw(
        target_user_id=user_id,
        actor_id=user_id,
        is_admin=False,
        username=username,
        phone=phone,
        address=address,
        bio=bio,
        avatar=avatar,
    )


def sp_user_change_password(
    user_id: str,
    new_password_hash: str,
):
    """
    Wrapper tương thích code cũ:
    - User tự đổi mật khẩu của chính mình.
    """
    return sp_user_change_password_raw(
        target_user_id=user_id,
        actor_id=user_id,
        is_admin=False,
        new_password_hash=new_password_hash,
    )
