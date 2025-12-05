# accounts/services/user_sp.py

from typing import Dict, Any

from django.contrib.auth import get_user_model
import json
from accounts.services.authz import is_admin_like, user_has_perm
from . import proc_user
from django.db import connection 
User = get_user_model()


def get_user_json(target_user_id: str):
    """
    Lấy thông tin user dạng JSON từ SP sp_user_get_json.
    """
    return proc_user.sp_user_get_json(target_user_id)


def update_own_profile(actor, data: dict):
    """
    User tự cập nhật hồ sơ của chính mình.
    Chỉ cần login, không check permission.
    SP sẽ đảm bảo chỉ update đúng id của actor.
    """
    with connection.cursor() as cursor:
        cursor.callproc(
            "sp_user_update_profile",
            [
                str(actor.id),              # p_target_user_id
                str(actor.id),              # p_actor_id
                0,                          # p_is_admin = 0 (user thường)
                data.get("username"),
                data.get("phone"),
                data.get("address"),
                data.get("bio"),
                data.get("avatar"),
            ],
        )
        row = cursor.fetchone()

    if not row:
        return {"error": "UNKNOWN_ERROR"}

    # SP đang SELECT JSON_OBJECT(...) AS result; hoặc sp_user_get_json(...)
    # giả sử nó trả về JSON string, huynh dùng thẳng row[0]
    return row[0]

def admin_update_user_profile(actor, target_user_id: str, data: dict):
    """
    Admin/Staff cập nhật hồ sơ cho user bất kỳ.
    Cần quyền 'user.manage'.
    """
    if not user_has_perm(actor, "user.manage"):
        raise PermissionError("NO_PERMISSION_MANAGE_USER")

    with connection.cursor() as cursor:
        cursor.callproc(
            "sp_user_update_profile",
            [
                str(target_user_id),        # p_target_user_id
                str(actor.id),              # p_actor_id
                1,                          # p_is_admin = 1 (admin/staff)
                data.get("username"),
                data.get("phone"),
                data.get("address"),
                data.get("bio"),
                data.get("avatar"),
            ],
        )
        row = cursor.fetchone()

    if not row:
        return {"error": "UNKNOWN_ERROR"}

    return row[0]

def change_own_password(actor, new_password_hash: str):
    """
    User (đang login) tự đổi mật khẩu chính mình.
    Không check user_has_perm, chỉ cần IsAuthenticated ở view.
    Admin/Staff/Fan cứng đều dùng flow này để đổi mật khẩu của chính họ.
    """
    with connection.cursor() as cursor:
        cursor.callproc(
            "sp_user_change_password",  # tên SP của huynh
            [
                str(actor.id),          # p_target_user_id
                str(actor.id),          # p_actor_id
                0,                      # p_is_admin = 0 (tự đổi của mình)
                new_password_hash,      # p_new_password_hash
            ],
        )
        row = cursor.fetchone()

    if not row:
        return {"error": "UNKNOWN_ERROR"}

    return row[0]  # JSON từ SP

def admin_reset_user_password(actor, target_user_id: str, new_password_hash: str):
    """
    Admin/staff reset mật khẩu cho user khác.
    """
    if not user_has_perm(actor, "user.reset_password"):
        raise PermissionError("NO_PERMISSION_RESET_PASSWORD")

    return proc_user.sp_user_change_password_raw(
        target_user_id=target_user_id,
        actor_id=actor.id,
        is_admin=is_admin_like(actor),
        new_password_hash=new_password_hash,
    )


def list_users_json(actor, q=None, is_active=None, page: int = 1, page_size: int = 20):
    """
    Danh sách user (JSON). Chỉ admin/staff có quyền.
    """
    # Check quyền 1 lần ở đây (có thể bỏ ở view nếu huynh muốn).
    if not user_has_perm(actor, "user.view"):
        raise PermissionError("NO_PERMISSION_VIEW_USERS")

    # Chuẩn hoá is_active trước khi truyền vào SP
    # None  -> không filter (NULL)
    # True  -> 1
    # False -> 0
    if is_active is True:
        is_active_param = 1
    elif is_active is False:
        is_active_param = 0
    else:
        is_active_param = None

    # Chuẩn hoá q: nếu chuỗi rỗng thì coi như không filter
    if q == "":
        q_param = None
    else:
        q_param = q

    with connection.cursor() as cursor:
        cursor.callproc(
            "sp_users_list_json",
            [
                q_param,           # p_q
                is_active_param,   # p_is_active
                page,              # p_page
                page_size,         # p_page_size
            ],
        )
        rows = cursor.fetchall()

    results = []
    for (raw_json,) in rows:
        try:
            obj = json.loads(raw_json)
        except Exception:
            obj = {"raw": raw_json}
        results.append(obj)

    return results