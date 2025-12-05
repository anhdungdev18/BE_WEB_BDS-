from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.contrib.auth.hashers import make_password
from ..services.proc_user import (
    sp_user_get_json, sp_user_update_profile, sp_user_change_password, sp_users_list_json
)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    data = sp_user_get_json(request.user.id)
    return Response(data)

@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_me(request):
    nz = lambda x: None if x in (None, "", "null") else x
    data = sp_user_update_profile(
        request.user.id,
        nz(request.data.get("username")),
        nz(request.data.get("so_dien_thoai")),
        nz(request.data.get("address")),
        nz(request.data.get("bio")),
        nz(request.data.get("anh_dai_dien")),
    )
    return Response(data)

@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def change_password(request):
    # nhận plaintext, hash ở Django, không đẩy plaintext xuống DB
    new_pw = request.data.get("new_password")
    if not new_pw:
        return Response({"error":"new_password required"}, status=400)
    new_hash = make_password(new_pw)
    data = sp_user_change_password(request.user.id, new_hash)
    return Response(data)

@api_view(["GET"])
@permission_classes([IsAdminUser])
def users_list(request):
    q = request.query_params.get("q")
    is_active = request.query_params.get("is_active")
    if is_active is not None:
        is_active = 1 if str(is_active) in ("1","true","True") else 0
    page = int(request.query_params.get("page", 1))
    size = int(request.query_params.get("page_size", 20))
    rows = sp_users_list_json(q, is_active, page, size)  # list các JSON_OBJECT
    return Response(rows)
