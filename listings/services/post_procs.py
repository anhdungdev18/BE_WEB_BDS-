# listings/services/post_procs.py

import json
from typing import Any, Dict, List, Optional

from django.db import connection


def _fetch_all_json(cursor) -> List[Dict[str, Any]]:
    rows = cursor.fetchall()
    if not rows:
        return []
    results: List[Dict[str, Any]] = []
    for row in rows:
        val = row[0]
        if isinstance(val, str):
            results.append(json.loads(val))
        else:
            results.append(val)
    return results


def _fetch_one_json(cursor) -> Optional[Dict[str, Any]]:
    row = cursor.fetchone()
    if not row:
        return None
    val = row[0]
    if isinstance(val, str):
        return json.loads(val)
    return val


# ========== CREATE ==========
def sp_post_create(
    actor_id: str,
    is_agent: int,  # 1 = AGENT, 0 = MEMBER/khác
    title: str,
    description: str,
    address_json: Dict[str, Any],
    location_json: Dict[str, Any],
    details_json: Dict[str, Any],
    other_info_json: Optional[Dict[str, Any]],
    area: float,
    price: float,
    post_type_id: int,
    category_id: int,
) -> Dict[str, Any]:
    """
    Gọi SP sp_post_create với thêm tham số is_agent.
    LƯU Ý: Thứ tự tham số phải khớp với định nghĩa SP trong MySQL:
        (p_actor_id, p_is_agent, p_title, p_description, ...)
    """
    with connection.cursor() as cur:
        cur.callproc(
            "sp_post_create",
            [
                actor_id,
                is_agent,
                title,
                description,
                json.dumps(address_json),
                json.dumps(location_json),
                json.dumps(details_json),
                json.dumps(other_info_json) if other_info_json is not None else None,
                area,
                price,
                post_type_id,
                category_id,
            ],
        )
        return _fetch_one_json(cur)


# ========== GET DETAIL ==========
def sp_post_get_json(post_id: str) -> Optional[Dict[str, Any]]:
    with connection.cursor() as cur:
        cur.callproc("sp_post_get_json", [post_id])
        return _fetch_one_json(cur)


# ========== UPDATE ==========
def sp_post_update(
    post_id: str,
    actor_id: str,
    is_admin: bool,
    title: Optional[str],
    description: Optional[str],
    address_json: Optional[Dict[str, Any]],
    location_json: Optional[Dict[str, Any]],
    details_json: Optional[Dict[str, Any]],
    other_info_json: Optional[Dict[str, Any]],
    area: Optional[float],
    price: Optional[float],
    post_type_id: Optional[int],
    category_id: Optional[int],
) -> Dict[str, Any]:
    with connection.cursor() as cur:
        cur.callproc(
            "sp_post_update",
            [
                post_id,
                actor_id,
                1 if is_admin else 0,
                title,
                description,
                json.dumps(address_json) if address_json is not None else None,
                json.dumps(location_json) if location_json is not None else None,
                json.dumps(details_json) if details_json is not None else None,
                json.dumps(other_info_json) if other_info_json is not None else None,
                area,
                price,
                post_type_id,
                category_id,
            ],
        )
        return _fetch_one_json(cur)


# ========== CHANGE STATUS ==========
def sp_post_change_status(
    post_id: str,
    actor_id: str,
    is_admin: bool,
    approval_status_id: Optional[int],
    post_status_id: Optional[int],
) -> Dict[str, Any]:
    with connection.cursor() as cur:
        cur.callproc(
            "sp_post_change_status",
            [
                post_id,
                actor_id,
                1 if is_admin else 0,
                approval_status_id,
                post_status_id,
            ],
        )
        return _fetch_one_json(cur)


# ========== SOFT DELETE ==========
def sp_post_soft_delete(
    post_id: str,
    actor_id: str,
    is_admin: bool,
) -> Dict[str, Any]:
    with connection.cursor() as cur:
        cur.callproc(
            "sp_post_soft_delete",
            [
                post_id,
                actor_id,
                1 if is_admin else 0,
            ],
        )
        return _fetch_one_json(cur)


# ========== SEARCH + COUNT ==========
def sp_posts_search(
    q: Optional[str],
    category_id: Optional[int],
    post_type_id: Optional[int],
    price_min: Optional[float],
    price_max: Optional[float],
    area_min: Optional[float],
    area_max: Optional[float],
    province: Optional[str],
    district: Optional[str],
    ward: Optional[str],
    sort: Optional[str],
    order: Optional[str],
    page: Optional[int],
    page_size: Optional[int],
):
    with connection.cursor() as cur:
        cur.callproc(
            "sp_posts_search",
            [
                q,
                category_id,
                post_type_id,
                price_min,
                price_max,
                area_min,
                area_max,
                province,
                district,
                ward,
                sort,
                order,
                page,
                page_size,
            ],
        )
        return _fetch_all_json(cur)


def sp_posts_count(
    q: Optional[str],
    category_id: Optional[int],
    post_type_id: Optional[int],
    price_min: Optional[float],
    price_max: Optional[float],
    area_min: Optional[float],
    area_max: Optional[float],
    province: Optional[str],
    district: Optional[str],
    ward: Optional[str],
) -> int:
    with connection.cursor() as cur:
        cur.callproc(
            "sp_posts_count",
            [
                q,
                category_id,
                post_type_id,
                price_min,
                price_max,
                area_min,
                area_max,
                province,
                district,
                ward,
            ],
        )
        data = _fetch_one_json(cur)
        if not data:
            return 0
        return int(data.get("total", 0))


def sp_posts_by_owner(
    owner_id: str,
    only_public: int = 1,
    page: int = 1,
    page_size: int = 20,
):
    """
    Lấy danh sách bài của 1 owner_id (dùng cho public page, profile, my posts).
    only_public = 1 -> chỉ bài đã Approved + Published
    """
    with connection.cursor() as cur:
        cur.callproc(
            "sp_posts_by_owner",
            [
                owner_id,
                only_public,
                page,
                page_size,
            ],
        )
        return _fetch_all_json(cur)
