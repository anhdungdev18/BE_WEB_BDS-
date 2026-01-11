from typing import Dict, Any, List
from django.db.models import Q
from listings.models import Post
from common.chroma_client import get_listings_collection
from common.openai_client import get_openai_client


def _apply_structured_filters(qs, filters: Dict[str, Any]):
    """
    Áp các điều kiện cứng từ NLU vào QuerySet.
    """
    qs = qs.filter(is_deleted=False)

    property_type = filters.get("property_type")
    if property_type:
        # TODO: Lọc theo loại BĐS nếu DB có field phù hợp.
        # Ví dụ nếu Category có field "name" chứa "Căn hộ", "Nhà phố", "Đất nền"
        # thì sau này huynh có thể map như:
        #
        # if property_type == "apartment":
        #     qs = qs.filter(category__name__icontains="căn hộ")
        # elif property_type == "house":
        #     qs = qs.filter(category__name__icontains="nhà")
        # elif property_type == "land":
        #     qs = qs.filter(category__name__icontains="đất")
        #
        # Hiện tại tạm THÔI KHÔNG filter gì ở đây để tránh lỗi slug.
        pass

    # city / district : address là JSON -> dùng contains text
    city = filters.get("city")
    district = filters.get("district")
    if city:
        qs = qs.filter(address__icontains=city)
    if district:
        qs = qs.filter(address__icontains=district)

    min_price = filters.get("min_price")
    max_price = filters.get("max_price")
    if min_price is not None:
        qs = qs.filter(price__gte=min_price)
    if max_price is not None:
        qs = qs.filter(price__lte=max_price)

    min_area = filters.get("min_area")
    max_area = filters.get("max_area")
    if min_area is not None:
        qs = qs.filter(area__gte=min_area)
    if max_area is not None:
        qs = qs.filter(area__lte=max_area)

    bedrooms_min = filters.get("bedrooms_min")
    if bedrooms_min is not None:
        # Tạm thời bỏ qua filter phòng ngủ (đang nằm trong JSON `details`)
        pass

    return qs



def db_only_search(filters: Dict[str, Any], limit: int = 20) -> List[Post]:
    qs = Post.objects.all()
    qs = _apply_structured_filters(qs, filters)
    return list(qs.order_by("-bumped_at", "-created_at")[:limit])


def semantic_search(user_query: str, limit: int = 20) -> List[Post]:
    client = get_openai_client()
    collection = get_listings_collection()

    emb = client.embeddings.create(
        model="text-embedding-3-large",
        input=[user_query],
    )
    vec = emb.data[0].embedding

    result = collection.query(
        query_embeddings=[vec],
        n_results=limit,
    )
    ids = result["ids"][0]  # list[str]

    return list(Post.objects.filter(id__in=ids, is_deleted=False))


def hybrid_search(user_query: str, filters: Dict[str, Any], limit: int = 20) -> List[Post]:
    # 1) DB pre-filter lấy pool
    qs = Post.objects.all()
    qs = _apply_structured_filters(qs, filters)
    candidate_ids = list(qs.values_list("id", flat=True)[:200])

    if not candidate_ids:
        return []

    # 2) Semantic search trong pool đó (lọc bằng metadata post_id)
    client = get_openai_client()
    collection = get_listings_collection()

    emb = client.embeddings.create(
        model="text-embedding-3-large",
        input=[user_query],
    )
    vec = emb.data[0].embedding

    result = collection.query(
        query_embeddings=[vec],
        n_results=limit,
        where={"post_id": {"$in": candidate_ids}},
    )

    ids = result["ids"][0]  # list[str]
    posts = list(Post.objects.filter(id__in=ids, is_deleted=False))

    # Giữ đúng thứ tự theo độ giống nhau mà Chroma trả về
    id_to_post = {p.id: p for p in posts}
    ordered = [id_to_post[i] for i in ids if i in id_to_post]
    return ordered
