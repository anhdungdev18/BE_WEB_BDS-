# accounts/services/user_sp.py

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
import json
from django.core.files.storage import default_storage
from django.conf import settings
from accounts.services.authz import is_admin_like, user_has_perm
from . import proc_user


JsonPayload = Union[str, dict]

def _normalize_avatar_url(value: str, request=None):
    """
    - Nếu đã là URL http(s) => giữ nguyên
    - Nếu là path/public_id => dùng default_storage.url(...) để ra URL (Cloudinary)
    - Nếu value đang có prefix media/ thì strip cho sạch trước khi đưa vào storage.url
    - Nếu có request thì build absolute cho trường hợp storage trả path tương đối
    """
    if not value:
        return None

    s = str(value).strip()
    if s.startswith("http://") or s.startswith("https://"):
        return s

    s = s.lstrip("/")

    media_url = (getattr(settings, "MEDIA_URL", "") or "").lstrip("/")
    if media_url and s.startswith(media_url):
        s = s[len(media_url):].lstrip("/")

    try:
        url = default_storage.url(s)  # ✅ CloudinaryStorage sẽ trả URL đầy đủ
    except Exception:
        # fallback: ít khi cần
        url = f"/{media_url.rstrip('/')}/{s}" if media_url else s

    if request and isinstance(url, str) and url.startswith("/"):
        try:
            return request.build_absolute_uri(url)
        except Exception:
            return url

    return url 
def _as_json_string(payload: Any) -> str:
    """
    Chuẩn hoá output về JSON string để tương thích code cũ:
    - Nếu payload là dict -> dumps
    - Nếu payload là str -> giữ nguyên
    - Nếu None -> JSON error
    """
    if payload is None:
        return json.dumps({"error": "UNKNOWN_ERROR"}, ensure_ascii=False)

    if isinstance(payload, str):
        return payload

    if isinstance(payload, dict):
        return json.dumps(payload, ensure_ascii=False)

    # fallback
    return json.dumps({"raw": str(payload)}, ensure_ascii=False)


def _as_dict(payload: Any) -> Dict[str, Any]:
    """
    Parse payload thành dict an toàn (dùng cho list).
    """
    if payload is None:
        return {"error": "UNKNOWN_ERROR"}

    if isinstance(payload, dict):
        return payload

    if isinstance(payload, str):
        try:
            return json.loads(payload)
        except Exception:
            return {"raw": payload}

    return {"raw": str(payload)}


def get_user_json(target_user_id: str) -> str:
    """
    Lấy thông tin user dạng JSON string từ SP sp_user_get_json.
    """
    return _as_json_string(proc_user.sp_user_get_json(str(target_user_id)))


def update_own_profile(actor, data: dict) -> str:
    """
    User tự cập nhật hồ sơ của chính mình.
    Trả về JSON string (tương thích code cũ).
    """
    payload = proc_user.sp_user_update_profile_raw(
        target_user_id=str(actor.id),
        actor_id=str(actor.id),
        is_admin=False,
        username=data.get("username"),
        phone=data.get("phone"),
        address=data.get("address"),
        bio=data.get("bio"),
        avatar=data.get("avatar"),
    )
    return _as_json_string(payload)


def admin_update_user_profile(actor, target_user_id: str, data: dict) -> str:
    """
    Admin/Staff cập nhật hồ sơ cho user bất kỳ.
    Cần quyền 'user.manage'.
    Trả về JSON string (tương thích code cũ).
    """
    if not user_has_perm(actor, "user.manage"):
        raise PermissionError("NO_PERMISSION_MANAGE_USER")

    payload = proc_user.sp_user_update_profile_raw(
        target_user_id=str(target_user_id),
        actor_id=str(actor.id),
        is_admin=True,  # hoặc is_admin_like(actor) cũng được
        username=data.get("username"),
        phone=data.get("phone"),
        address=data.get("address"),
        bio=data.get("bio"),
        avatar=data.get("avatar"),
    )
    return _as_json_string(payload)


def change_own_password(actor, new_password_hash: str) -> str:
    """
    User tự đổi mật khẩu chính mình.
    Trả về JSON string.
    """
    payload = proc_user.sp_user_change_password_raw(
        target_user_id=str(actor.id),
        actor_id=str(actor.id),
        is_admin=False,
        new_password_hash=new_password_hash,
    )
    return _as_json_string(payload)


def admin_reset_user_password(actor, target_user_id: str, new_password_hash: str) -> str:
    """
    Admin/staff reset mật khẩu cho user khác.
    Trả về JSON string.
    """
    if not user_has_perm(actor, "user.reset_password"):
        raise PermissionError("NO_PERMISSION_RESET_PASSWORD")

    payload = proc_user.sp_user_change_password_raw(
        target_user_id=str(target_user_id),
        actor_id=str(actor.id),
        is_admin=is_admin_like(actor),
        new_password_hash=new_password_hash,
    )
    return _as_json_string(payload)


def list_users_json(actor, q=None, is_active=None, page: int = 1, page_size: int = 20) -> List[Dict[str, Any]]:
    """
    Danh sách user (list dict). Chỉ admin/staff có quyền.
    """
    if not user_has_perm(actor, "user.view"):
        raise PermissionError("NO_PERMISSION_VIEW_USERS")

    # Chuẩn hoá is_active: True->1, False->0, None->None
    if is_active is True:
        is_active_param = 1
    elif is_active is False:
        is_active_param = 0
    else:
        is_active_param = None

    # Chuẩn hoá q: "" -> None
    q_param = None if q == "" else q

    rows = proc_user.sp_users_list_json(
        q=q_param,
        is_active=is_active_param,
        page=page,
        page_size=page_size,
    )

    # proc_user có thể trả list[str] hoặc list[dict] tuỳ driver -> chuẩn hoá về dict
    results = []
    for item in rows or []:
        obj = _as_dict(item)  # hàm parse JSON của huynh
        if isinstance(obj, dict):
            # ✅ normalize avatar
            obj["anh_dai_dien"] = _normalize_avatar_url(obj.get("anh_dai_dien"))
        results.append(obj)

    return results