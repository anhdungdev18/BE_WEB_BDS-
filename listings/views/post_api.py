# listings/views/post_api.py

from typing import Optional

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.permissions import AllowAny
from listings.services import post_procs
from listings.services.auth_helpers import (
    get_actor_id,
    get_is_admin_flag,
    user_has_perm,
)


def _to_int(value: Optional[str]):
    if value in [None, ""]:
        return None
    return int(value)


def _to_float(value: Optional[str]):
    if value in [None, ""]:
        return None
    return float(value)


class PostListCreateView(APIView):
    """
    GET: search posts (public)
    POST: create post (user có perm 'post.create')
    """

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get(self, request, *args, **kwargs):
        params = request.query_params

        q = params.get("q")
        category_id = _to_int(params.get("category_id"))
        post_type_id = _to_int(params.get("post_type_id"))
        price_min = _to_float(params.get("price_min"))
        price_max = _to_float(params.get("price_max"))
        area_min = _to_float(params.get("area_min"))
        area_max = _to_float(params.get("area_max"))
        province = params.get("province")
        district = params.get("district")
        ward = params.get("ward")
        sort = params.get("sort")
        order = params.get("order")
        page = _to_int(params.get("page")) or 1
        page_size = _to_int(params.get("page_size")) or 20

        items = post_procs.sp_posts_search(
            q=q,
            category_id=category_id,
            post_type_id=post_type_id,
            price_min=price_min,
            price_max=price_max,
            area_min=area_min,
            area_max=area_max,
            province=province,
            district=district,
            ward=ward,
            sort=sort,
            order=order,
            page=page,
            page_size=page_size,
        )
        total = post_procs.sp_posts_count(
            q=q,
            category_id=category_id,
            post_type_id=post_type_id,
            price_min=price_min,
            price_max=price_max,
            area_min=area_min,
            area_max=area_max,
            province=province,
            district=district,
            ward=ward,
        )

        return Response(
            {
                "total": total,
                "page": page,
                "page_size": page_size,
                "results": items,
            }
        )

    def post(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return Response(
                {"detail": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # AGENT / MEMBER có post.create (SUPER_ADMIN full)
        if not user_has_perm(user, "post.create"):
            return Response(
                {"detail": "Bạn không có quyền tạo bài (post.create)"},
                status=status.HTTP_403_FORBIDDEN,
            )

        actor_id = get_actor_id(user)
        data = request.data

        address_json = data.get("address", {}) or {}
        location_json = data.get("location", {}) or {}
        details_json = data.get("details", {}) or {}
        other_info_json = data.get("other_info", {}) or {}

        try:
            area = _to_float(str(data.get("area")))
            price = _to_float(str(data.get("price")))
        except (TypeError, ValueError):
            return Response(
                {"detail": "area/price không hợp lệ"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        post_type_id = int(data["post_type_id"])
        category_id = int(data["category_id"])

        result = post_procs.sp_post_create(
            actor_id=actor_id,
            title=data.get("title"),
            description=data.get("description"),
            address_json=address_json,
            location_json=location_json,
            details_json=details_json,
            other_info_json=other_info_json,
            area=area,
            price=price,
            post_type_id=post_type_id,
            category_id=category_id,
        )
        return Response(result, status=status.HTTP_201_CREATED)


class PostDetailView(APIView):
    """
    GET: chi tiết post
    PATCH: update (owner hoặc admin-like)
    DELETE: soft delete (owner hoặc admin-like)
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, post_id: str, *args, **kwargs):
        post = post_procs.sp_post_get_json(post_id)
        if not post:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(post)

    def patch(self, request, post_id: str, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return Response(
                {"detail": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        actor_id = get_actor_id(user)
        is_admin_flag = get_is_admin_flag(user)

        # Quy ước:
        # - SUPER_ADMIN / STAFF (admin-like): được sửa mọi bài (SP sẽ cho vì p_is_admin=1).
        # - AGENT / MEMBER: cần perm post.update_own, SP kiểm tra đúng chính chủ.
        if not is_admin_flag:
            if not user_has_perm(user, "post.update_own"):
                return Response(
                    {"detail": "Không có quyền sửa bài của mình (post.update_own)"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        data = request.data

        title = data.get("title")
        description = data.get("description")

        address_json = data.get("address") if "address" in data else None
        location_json = data.get("location") if "location" in data else None
        details_json = data.get("details") if "details" in data else None
        other_info_json = data.get("other_info") if "other_info" in data else None

        area = _to_float(str(data["area"])) if "area" in data else None
        price = _to_float(str(data["price"])) if "price" in data else None
        post_type_id = _to_int(data.get("post_type_id")) if "post_type_id" in data else None
        category_id = _to_int(data.get("category_id")) if "category_id" in data else None

        result = post_procs.sp_post_update(
            post_id=post_id,
            actor_id=actor_id,
            is_admin=bool(is_admin_flag),
            title=title,
            description=description,
            address_json=address_json,
            location_json=location_json,
            details_json=details_json,
            other_info_json=other_info_json,
            area=area,
            price=price,
            post_type_id=post_type_id,
            category_id=category_id,
        )

        if result and result.get("error") == "NOT_ALLOWED_OR_NOT_FOUND":
            # Có thể do không phải chủ bài & không phải admin-like
            return Response(result, status=status.HTTP_403_FORBIDDEN)

        if not result:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response(result)

    def delete(self, request, post_id: str, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return Response(
                {"detail": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        actor_id = get_actor_id(user)
        is_admin_flag = get_is_admin_flag(user)

        # SUPER_ADMIN/STAFF: cho phép xóa mọi bài (SP kiểm tra p_is_admin=1).
        # AGENT/MEMBER: cần perm post.delete_soft_own + chính chủ.
        if not is_admin_flag:
            if not user_has_perm(user, "post.delete_soft_own"):
                return Response(
                    {"detail": "Không có quyền xóa bài của mình (post.delete_soft_own)"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        result = post_procs.sp_post_soft_delete(
            post_id=post_id,
            actor_id=actor_id,
            is_admin=bool(is_admin_flag),
        )

        if result and result.get("error") == "NOT_ALLOWED_OR_NOT_FOUND":
            return Response(result, status=status.HTTP_403_FORBIDDEN)

        return Response(result, status=status.HTTP_200_OK)


class PostStatusChangeView(APIView):
    """
    PATCH: đổi approval_status / post_status (chỉ SUPER_ADMIN/STAFF – admin-like)
    body:
    {
      "approval_status_id": 2,
      "post_status_id": 1
    }
    """
    permission_classes = [permissions.IsAuthenticated]

    # Huynh chỉnh lại 2 hằng số này theo id thực tế trong bảng listings_approvalstatus
    ID_APPROVED = 2
    ID_REJECTED = 3

    def patch(self, request, post_id: str, *args, **kwargs):
        user = request.user
        actor_id = get_actor_id(user)
        is_admin_flag = get_is_admin_flag(user)

        # Chỉ SUPER_ADMIN/STAFF
        if not is_admin_flag:
            return Response(
                {"detail": "Chỉ SUPER_ADMIN/STAFF mới được đổi trạng thái bài"},
                status=status.HTTP_403_FORBIDDEN,
            )

        data = request.data
        approval_status_id = _to_int(data.get("approval_status_id"))
        post_status_id = _to_int(data.get("post_status_id"))

        # Nếu chuyển sang Approved -> cần post.approve
        if approval_status_id == self.ID_APPROVED:
            if not user_has_perm(user, "post.approve"):
                return Response(
                    {"detail": "Thiếu quyền duyệt bài (post.approve)"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        # Nếu chuyển sang Rejected -> cần post.reject
        if approval_status_id == self.ID_REJECTED:
            if not user_has_perm(user, "post.reject"):
                return Response(
                    {"detail": "Thiếu quyền từ chối bài (post.reject)"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        # Các thay đổi trạng thái khác: có thể chỉ cần post.view_all
        if approval_status_id not in (self.ID_APPROVED, self.ID_REJECTED) and approval_status_id is not None:
            if not user_has_perm(user, "post.view_all"):
                return Response(
                    {"detail": "Thiếu quyền xem & quản lý tất cả bài (post.view_all)"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        result = post_procs.sp_post_change_status(
            post_id=post_id,
            actor_id=actor_id,
            is_admin=bool(is_admin_flag),
            approval_status_id=approval_status_id,
            post_status_id=post_status_id,
        )

        if result and result.get("error") == "NOT_ALLOWED_OR_NOT_FOUND":
            return Response(result, status=status.HTTP_404_NOT_FOUND)

        return Response(result)
class OwnerPostListView(APIView):
    """
    GET /api/listings/owner-posts/?owner_id=&page=&page_size=&only_public=

    - Ai cũng xem được (AllowAny)
    - Dùng để:
        + Trang cá nhân public của user khác
        + Trang my-posts của chính mình (FE tự truyền owner_id = id của mình)
    """

    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        params = request.query_params

        owner_id = params.get("owner_id")
        if not owner_id:
            return Response(
                {"detail": "owner_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        page = _to_int(params.get("page")) or 1
        page_size = _to_int(params.get("page_size")) or 20

        only_public_raw = params.get("only_public", "1")
        only_public = 1 if only_public_raw in ["1", "true", "True"] else 0

        items = post_procs.sp_posts_by_owner(
            owner_id=owner_id,
            only_public=only_public,
            page=page,
            page_size=page_size,
        )
        return Response(
            {
                "page": page,
                "page_size": page_size,
                "results": items,
            },
            status=status.HTTP_200_OK,
        )