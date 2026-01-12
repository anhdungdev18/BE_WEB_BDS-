# accounts/services/proc_user.py

from __future__ import annotations

import json
from typing import Optional, Any, Union, List
from django.db import connection


JsonPayload = Union[str, dict]


def _fetch_one_json(cur) -> Optional[JsonPayload]:
    """
    SP user_* thường SELECT JSON_OBJECT(...) AS result
    -> lấy cột result của dòng đầu tiên.
    """
    row = cur.fetchone()
    return None if not row else row[0]  # alias 'result'


def _looks_like_user_obj(d: Any) -> bool:
    """
    Chỉ bơm field avatar cho payload có vẻ là user object.
    Tránh bơm nhầm vào các payload error kiểu {"error": "..."}.
    """
    return isinstance(d, dict) and any(k in d for k in ("id", "email", "username"))


def _ensure_user_avatar_key(payload: Optional[JsonPayload], key: str = "anh_dai_dien") -> Optional[JsonPayload]:
    """
    Đảm bảo JSON user luôn có key `anh_dai_dien` (giá trị None nếu chưa có).
    - Nếu payload là str JSON -> parse -> bơm key -> dump lại string
    - Nếu payload là dict -> bơm trực tiếp
    """
    if payload is None:
        return None

    # Nếu DB driver trả dict sẵn
    if isinstance(payload, dict):
        if _looks_like_user_obj(payload) and key not in payload:
            payload[key] = None
        return payload

    # Nếu DB driver trả string JSON
    if isinstance(payload, str):
        try:
            data = json.loads(payload)
        except Exception:
            # Không parse được thì trả nguyên (đỡ làm hỏng dữ liệu)
            return payload

        if _looks_like_user_obj(data) and key not in data:
            data[key] = None

        return json.dumps(data, ensure_ascii=False)

    return payload


def sp_user_get_json(user_id: str):
    """
    Gọi SP sp_user_get_json(user_id) -> trả JSON thông tin user.
    """
    with connection.cursor() as cur:
        cur.callproc("sp_user_get_json", [user_id])
        return _ensure_user_avatar_key(_fetch_one_json(cur))


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
    Wrapper cho SP sp_user_update_profile:

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

    Ghi chú:
    - Truyền None nghĩa là "không đổi" (SP nên dùng COALESCE).
    - Truyền "" (chuỗi rỗng) nếu muốn "xoá" giá trị (tuỳ FE/logic).
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
        return _ensure_user_avatar_key(_fetch_one_json(cur))


def sp_user_change_password_raw(
    target_user_id: str,
    actor_id: str,
    is_admin: bool,
    new_password_hash: str,
):
    """
    Wrapper cho SP sp_user_change_password .
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


def sp_users_list_json(q=None, is_active=None, page: int = 1, page_size: int = 20) -> List[JsonPayload]:
    """
    Wrapper cho SP sp_users_list_json, trả list JSON (mỗi hàng là 1 JSON_OBJECT).
    Đảm bảo mỗi item (nếu là user object) có `anh_dai_dien`.
    """
    with connection.cursor() as cur:
        cur.callproc("sp_users_list_json", [q, is_active, page, page_size])
        rows = [r[0] for r in cur.fetchall()]
        return [_ensure_user_avatar_key(x) for x in rows]


def sp_user_update_profile(
    user_id: str,
    username=None,
    phone=None,
    address=None,
    bio=None,
    avatar=None,
):
    """
    User tự sửa hồ sơ của chính mình.
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
    User tự đổi mật khẩu của chính mình.
    """
    return sp_user_change_password_raw(
        target_user_id=user_id,
        actor_id=user_id,
        is_admin=False,
        new_password_hash=new_password_hash,
    )
