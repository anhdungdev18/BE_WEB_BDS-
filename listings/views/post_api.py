# listings/views/post_api.py

from typing import Optional
import json

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from listings.services.bump_services import bump_post_for_request

from listings.services import post_procs
from listings.services.auth_helpers import (
    get_actor_id,
    get_is_admin_flag,
    has_perm,
    is_agent,
)

from listings.models import Post, PostImage
from listings.serializers import PostImageSerializer


def _to_int(value: Optional[str]):
    if value in [None, ""]:
        return None
    return int(value)


def _to_float(value: Optional[str]):
    if value in [None, ""]:
        return None
    return float(value)


def _parse_json_field(data, key, default=None, allow_missing=True):
    """
    Hỗ trợ cả 2 trường hợp:
    - request JSON: data[key] là dict/list
    - request multipart/form-data: data[key] là string JSON
    """
    if allow_missing and key not in data:
        return default

    raw = data.get(key)
    if raw in [None, ""]:
        return default

    # Nếu đã là dict/list (request JSON)
    if isinstance(raw, (dict, list)):
        return raw

    # Nếu là string -> cố gắng parse JSON
    try:
        return json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        raise ValueError(f"{key} must be valid JSON")


class PostListCreateView(APIView):
    """
    GET: search posts (public)
    POST: create post (user có perm 'post.create') + upload images
    """

    parser_classes = [JSONParser, FormParser, MultiPartParser]

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

        # ===== GẮN ẢNH CHO TỪNG POST =====
        post_ids = [
            item["id"]
            for item in items
            if isinstance(item, dict) and "id" in item
        ]

        image_map = {}
        if post_ids:
            images_qs = PostImage.objects.filter(
                post_id__in=post_ids
            ).order_by("created_at")

            # build map: post_id -> [images...]
            for img in images_qs:
                data = PostImageSerializer(
                    img,
                    context={"request": request},
                ).data
                key = str(img.post_id)
                image_map.setdefault(key, []).append(data)

        # gắn images vào từng item
        for item in items:
            if isinstance(item, dict):
                pid = str(item.get("id"))
                item["images"] = image_map.get(pid, [])

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
        # 1) Check đăng nhập
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # 2) Check permission tạo bài
        if not has_perm(request, "post.create"):
            return Response(
                {"detail": "Bạn không có quyền tạo bài (post.create)"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # 3) Lấy actor_id (id user) & flag agent
        actor_id = get_actor_id(request)
        if not actor_id:
            return Response(
                {"detail": "Không xác định được người dùng (actor_id)"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        is_agent_flag = 1 if is_agent(request) else 0
        data = request.data

        # 3.1) Lấy danh sách file ảnh gửi lên
        if hasattr(request.data, "getlist"):
            files = request.data.getlist("images")
        else:
            files = request.FILES.getlist("images")

        # Lọc bỏ None / file rỗng
        valid_files = [f for f in files if f]

        # 3.2) Áp hạn mức số ảnh theo role
        max_images = 10 if is_agent_flag == 1 else 6
        if len(valid_files) > max_images:
            return Response(
                {
                    "ok": 0,
                    "error": "MAX_IMAGES_PER_POST_REACHED",
                    "message": (
                        "Bạn chỉ được upload tối đa "
                        f"{max_images} ảnh cho mỗi bài đăng "
                        + ("(AGENT: 10, MEMBER: 6)." if max_images == 10 else "(MEMBER: 6).")
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---- Parse JSON fields (hỗ trợ cả JSON & multipart) ----
        try:
            address_json = _parse_json_field(
                data, "address", default={}, allow_missing=False
            )
            location_json = _parse_json_field(
                data, "location", default={}, allow_missing=False
            )
            details_json = _parse_json_field(
                data, "details", default={}, allow_missing=False
            )
            other_info_json = _parse_json_field(
                data, "other_info", default={}, allow_missing=True
            )
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # area & price
        try:
            area = _to_float(str(data.get("area")))
            price = _to_float(str(data.get("price")))
        except (TypeError, ValueError):
            return Response(
                {"detail": "area/price không hợp lệ"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if area is None or price is None:
            return Response(
                {"detail": "area và price là bắt buộc"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # post_type & category
        try:
            post_type_id = int(data["post_type_id"])
            category_id = int(data["category_id"])
        except (KeyError, ValueError, TypeError):
            return Response(
                {"detail": "post_type_id/category_id không hợp lệ"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ====== GỌI SP TẠO BÀI ======
        result = post_procs.sp_post_create(
            actor_id=actor_id,
            is_agent=is_agent_flag,
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

        # Nếu SP trả lỗi dạng { ok: 0, ... } (vd: MAX_DAILY_POSTS_REACHED)
        if isinstance(result, dict) and result.get("ok") == 0:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        post_id = result.get("id") if isinstance(result, dict) else None
        if not post_id:
            # Trường hợp hiếm: SP không trả id nhưng cũng không báo ok=0
            return Response(result, status=status.HTTP_201_CREATED)

        # ====== TẠO ẢNH (PostImage) CHO BÀI VỪA TẠO ======
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response(result, status=status.HTTP_201_CREATED)

        # Dùng lại valid_files đã lấy ở trên (đã check limit)
        for f in valid_files:
            PostImage.objects.create(post=post, image=f)

        # ====== GẮN LIST ẢNH VÀO RESPONSE ======
        if isinstance(result, dict):
            images_qs = PostImage.objects.filter(post=post)
            result["images"] = PostImageSerializer(
                images_qs,
                many=True,
                context={"request": request},
            ).data

        return Response(result, status=status.HTTP_201_CREATED)

class PostDetailView(APIView):
    """
    GET: chi tiết post + danh sách ảnh
    PATCH: update (owner hoặc admin-like) + thêm/xoá ảnh
    DELETE: soft delete (owner hoặc admin-like)
    """

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def get(self, request, post_id: str, *args, **kwargs):
        data = post_procs.sp_post_get_json(post_id)
        if not data:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        # Gắn thêm images từ ORM
        try:
            post_obj = Post.objects.get(id=post_id)
            images_qs = PostImage.objects.filter(post=post_obj)
            images_data = PostImageSerializer(
                images_qs,
                many=True,
                context={"request": request},
            ).data

            if isinstance(data, dict):
                data["images"] = images_data
        except Post.DoesNotExist:
            pass

        return Response(data)

    def patch(self, request, post_id: str, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        actor_id = get_actor_id(request)
        is_admin_flag = get_is_admin_flag(request)

        # SUPER_ADMIN / STAFF được sửa mọi bài (SP xem p_is_admin=1).
        # AGENT / MEMBER: cần perm post.update_own, SP kiểm tra chính chủ.
        if not is_admin_flag:
            if not has_perm(request, "post.update_own"):
                return Response(
                    {"detail": "Không có quyền sửa bài của mình (post.update_own)"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        data = request.data

        title = data.get("title")
        description = data.get("description")

        # ---- Parse JSON fields (nếu field có trong request) ----
        try:
            address_json = _parse_json_field(
                data, "address", default=None, allow_missing=True
            )
            location_json = _parse_json_field(
                data, "location", default=None, allow_missing=True
            )
            details_json = _parse_json_field(
                data, "details", default=None, allow_missing=True
            )
            other_info_json = _parse_json_field(
                data, "other_info", default=None, allow_missing=True
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        area = _to_float(str(data["area"])) if "area" in data else None
        price = _to_float(str(data["price"])) if "price" in data else None
        post_type_id = _to_int(data.get("post_type_id")) if "post_type_id" in data else None
        category_id = _to_int(data.get("category_id")) if "category_id" in data else None

        # ====== GỌI SP UPDATE BÀI ======
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
            return Response(result, status=status.HTTP_403_FORBIDDEN)

        if not result:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        # ====== SAU KHI UPDATE THÀNH CÔNG: XỬ LÝ ẢNH ======
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response(result)

        # 1) Xoá ảnh theo delete_image_ids (optional)
        delete_raw = data.get("delete_image_ids")
        if delete_raw:
            try:
                if isinstance(delete_raw, str):
                    delete_ids = json.loads(delete_raw)
                else:
                    delete_ids = delete_raw
                if isinstance(delete_ids, list) and delete_ids:
                    PostImage.objects.filter(post=post, id__in=delete_ids).delete()
            except (TypeError, ValueError, json.JSONDecodeError):
                pass

        # 2) Thêm ảnh mới (images)
        if hasattr(request.data, "getlist"):
            files = request.data.getlist("images")
        else:
            files = request.FILES.getlist("images")

        new_images = []
        for f in files:
            if not f:
                continue
            img = PostImage.objects.create(post=post, image=f)
            new_images.append(
                PostImageSerializer(img, context={"request": request}).data
            )

        # 3) Trả lại result + danh sách ảnh hiện tại
        all_images = PostImageSerializer(
            PostImage.objects.filter(post=post),
            many=True,
            context={"request": request},
        ).data

        if isinstance(result, dict):
            result["images"] = all_images
            result["new_images"] = new_images

        return Response(result)

    def delete(self, request, post_id: str, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        actor_id = get_actor_id(request)
        is_admin_flag = get_is_admin_flag(request)

        # SUPER_ADMIN/STAFF: cho phép xóa mọi bài (SP kiểm tra p_is_admin=1).
        # AGENT/MEMBER: cần perm post.delete_soft_own + chính chủ.
        if not is_admin_flag:
            if not has_perm(request, "post.delete_soft_own"):
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
        actor_id = get_actor_id(request)
        is_admin_flag = get_is_admin_flag(request)

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
            if not has_perm(request, "post.approve"):
                return Response(
                    {"detail": "Thiếu quyền duyệt bài (post.approve)"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        # Nếu chuyển sang Rejected -> cần post.reject
        if approval_status_id == self.ID_REJECTED:
            if not has_perm(request, "post.reject"):
                return Response(
                    {"detail": "Thiếu quyền từ chối bài (post.reject)"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        # Các thay đổi trạng thái khác: có thể chỉ cần post.view_all
        if (
            approval_status_id not in (self.ID_APPROVED, self.ID_REJECTED)
            and approval_status_id is not None
        ):
            if not has_perm(request, "post.view_all"):
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

    permission_classes = [permissions.AllowAny]

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

        # ===== GẮN ẢNH CHO TỪNG POST =====
        post_ids = [
            item["id"]
            for item in items
            if isinstance(item, dict) and "id" in item
        ]

        image_map = {}
        if post_ids:
            images_qs = PostImage.objects.filter(
                post_id__in=post_ids
            ).order_by("created_at")

            for img in images_qs:
                data = PostImageSerializer(
                    img,
                    context={"request": request},
                ).data
                key = str(img.post_id)
                image_map.setdefault(key, []).append(data)

        for item in items:
            if isinstance(item, dict):
                pid = str(item.get("id"))
                item["images"] = image_map.get(pid, [])

        return Response(
            {
                "page": page,
                "page_size": page_size,
                "results": items,
            },
            status=status.HTTP_200_OK,
        )

class PostBumpView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, post_id: str, *args, **kwargs):
        # Tìm post
        try:
            post = Post.objects.get(id=post_id, is_deleted=False)
        except Post.DoesNotExist:
            return Response(
                {"ok": 0, "error": "NOT_FOUND", "message": "Bài đăng không tồn tại."},
                status=status.HTTP_404_NOT_FOUND,
            )

        result = bump_post_for_request(post, request.user)

        if not isinstance(result, dict):
            return Response(
                {"ok": 0, "error": "UNKNOWN_ERROR"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if result.get("ok") == 0:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        return Response(result, status=status.HTTP_200_OK)
