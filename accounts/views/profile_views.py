# accounts/views/profile_views.py

import json
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.contrib.auth.hashers import make_password

from ..services.proc_user import (
    sp_user_get_json,
    sp_user_update_profile,
    sp_user_change_password,
    sp_users_list_json,
)


def _maybe_load_json(raw):
    """Nếu raw là JSON string -> loads về dict/list. Nếu đã là dict/list -> giữ nguyên."""
    if raw is None:
        return None
    if isinstance(raw, (dict, list)):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except Exception:
            return raw
    return raw


def _ensure_avatar_key(obj):
    """Đảm bảo có key anh_dai_dien (nếu payload là dict user)."""
    if isinstance(obj, dict) and "anh_dai_dien" not in obj:
        obj["anh_dai_dien"] = None
    return obj


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    raw = sp_user_get_json(request.user.id)
    data = _maybe_load_json(raw)
    data = _ensure_avatar_key(data) if isinstance(data, dict) else data
    return Response(data)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_me(request):
    nz = lambda x: None if x in (None, "", "null") else x

    # nhận cả 2 key để khỏi lệch giữa FE/API khác nhau
    avatar_val = request.data.get("anh_dai_dien")
    if avatar_val in (None, "", "null"):
        avatar_val = request.data.get("avatar")

    raw = sp_user_update_profile(
        request.user.id,
        nz(request.data.get("username")),
        nz(request.data.get("so_dien_thoai")),
        nz(request.data.get("address")),
        nz(request.data.get("bio")),
        nz(avatar_val),
    )
    data = _maybe_load_json(raw)
    data = _ensure_avatar_key(data) if isinstance(data, dict) else data
    return Response(data)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def change_password(request):
    new_pw = request.data.get("new_password")
    if not new_pw:
        return Response({"error": "new_password required"}, status=400)

    new_hash = make_password(new_pw)
    raw = sp_user_change_password(request.user.id, new_hash)
    data = _maybe_load_json(raw)
    return Response(data)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def users_list(request):
    q = request.query_params.get("q")
    is_active = request.query_params.get("is_active")
    if is_active is not None:
        is_active = 1 if str(is_active) in ("1", "true", "True") else 0

    page = int(request.query_params.get("page", 1))
    size = int(request.query_params.get("page_size", 20))

    rows = sp_users_list_json(q, is_active, page, size)  # list các JSON_OBJECT (thường là string)

    results = []
    for item in rows or []:
        obj = _maybe_load_json(item)
        if isinstance(obj, dict):
            obj = _ensure_avatar_key(obj)
        results.append(obj)

    return Response(results)
