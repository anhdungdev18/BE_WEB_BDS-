# listings/services/auth_helpers.py

from typing import List, Optional
from rest_framework.request import Request


def _get_token(request: Request):
    """
    Lấy access token đã decode từ SimpleJWT.
    Mặc định nó nằm ở request.auth.
    """
    return getattr(request, "auth", None)


def get_actor_id(request: Request) -> Optional[str]:
    """
    Trả về id user hiện tại (dùng cho SP: p_user_id / p_actor_id).
    Ưu tiên lấy từ request.user, fallback về claim "user_id" trong token.
    """
    user = getattr(request, "user", None)
    if user is not None and getattr(user, "is_authenticated", False):
        return str(user.id)

    token = _get_token(request)
    if token is not None:
        try:
            uid = token.get("user_id")  # SimpleJWT claim mặc định
            if uid is not None:
                return str(uid)
        except Exception:
            pass

    return None


def get_roles(request: Request) -> List[str]:
    """
    Lấy danh sách role từ JWT (claim 'roles').
    Nếu không có thì fallback sang user.roles (ManyToMany) nếu dùng chung DB.
    """
    token = _get_token(request)

    if token is not None:
        try:
            roles = token.get("roles", [])  # type: ignore[attr-defined]
            if roles:
                return list(roles)
        except Exception:
            pass

    user = getattr(request, "user", None)
    if user is not None and hasattr(user, "roles"):
        return list(user.roles.values_list("role_name", flat=True))

    return []


def get_perms(request: Request) -> List[str]:
    """
    Lấy danh sách permission code từ JWT (claim 'perms').
    """
    token = _get_token(request)

    if token is not None:
        try:
            perms = token.get("perms", [])  # type: ignore[attr-defined]
            if perms:
                return list(perms)
        except Exception:
            pass

    return []


def has_perm(request: Request, perm_code: str) -> bool:
    """
    Check user có permission code nào đó hay không (theo token).
    """
    return perm_code in get_perms(request)


def is_agent(request: Request) -> bool:
    """
    Kiểm tra user có phải AGENT hay không.
    Ưu tiên claim 'is_agent', nếu không có thì nhìn vào roles.
    """
    token = _get_token(request)

    if token is not None:
        try:
            if token.get("is_agent", False):  # type: ignore[attr-defined]
                return True
        except Exception:
            pass

    roles = get_roles(request)
    return "AGENT" in roles


def is_admin(request: Request) -> bool:
    """
    SUPER_ADMIN được coi là admin hệ thống.
    """
    roles = get_roles(request)
    return "SUPER_ADMIN" in roles


def is_staff(request: Request) -> bool:
    """
    STAFF hoặc SUPER_ADMIN đều coi là staff (vận hành / duyệt tin).
    """
    roles = get_roles(request)
    return "STAFF" in roles or "SUPER_ADMIN" in roles


# 🔥 Các helper dạng "flag" dùng để truyền vào SP MySQL (0/1)


def get_is_admin_flag(request: Request) -> int:
    """
    Flag p_is_admin cho SP.
    Thường huynh dùng nghĩa: STAFF hoặc SUPER_ADMIN => 1, còn lại 0.
    """
    return 1 if is_staff(request) or is_admin(request) else 0


def get_is_staff_flag(request: Request) -> int:
    """
    Nếu sau này huynh cần riêng flag staff.
    """
    return 1 if is_staff(request) else 0
