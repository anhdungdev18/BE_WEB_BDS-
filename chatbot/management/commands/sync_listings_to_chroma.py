from django.core.management.base import BaseCommand
from listings.models import Post
from common.openai_client import get_openai_client
from common.chroma_client import get_listings_collection

import numbers

BATCH_SIZE = 64  # chỉnh tuỳ data

def json_to_text(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, numbers.Number):
        return str(value)
    if isinstance(value, dict):
        parts = []
        for k, v in value.items():
            t = json_to_text(v)
            if t:
                parts.append(f"{k}: {t}")
        return ", ".join(parts)
    if isinstance(value, (list, tuple)):
        parts = [json_to_text(v) for v in value]
        return ", ".join([p for p in parts if p])
    return str(value)


class Command(BaseCommand):
    help = "Sync Post (chưa xoá) sang Chroma để semantic search + xoá doc của bài đã xoá"

    def handle(self, *args, **options):
        client = get_openai_client()
        collection = get_listings_collection()

        # (A) XÓA khỏi Chroma các bài đã soft-delete
        deleted_ids = list(
            Post.objects.filter(is_deleted=True).values_list("id", flat=True)
        )
        if deleted_ids:
            collection.delete(ids=[str(x) for x in deleted_ids])
            self.stdout.write(self.style.WARNING(f"Đã xoá {len(deleted_ids)} doc khỏi Chroma (is_deleted=1)"))

        # (B) LẤY các bài còn sống để upsert
        posts = Post.objects.filter(is_deleted=False).order_by("created_at")

        if not posts.exists():
            self.stdout.write(self.style.WARNING("Không có Post nào để sync"))
            return

        ids, docs, metadatas = [], [], []

        # dùng iterator để đỡ ngốn RAM
        for p in posts.iterator():
            addr_text   = json_to_text(p.address)
            loc_text    = json_to_text(p.location)
            detail_text = json_to_text(p.details)
            other_text  = json_to_text(p.other_info)

            district = None
            city = None
            if isinstance(p.address, dict):
                district = p.address.get("district") or p.address.get("district_name")
                city = (
                    p.address.get("city")
                    or p.address.get("province")
                    or p.address.get("province_name")
                )

            pid = str(p.id)
            ids.append(pid)

            docs.append(
                f"Mã tin {pid}. {p.title}\n"
                f"Mô tả: {p.description or ''}\n"
                f"Địa chỉ: {addr_text}\n"
                f"Vị trí: {loc_text}\n"
                f"Chi tiết: {detail_text}\n"
                f"Thông tin khác: {other_text}\n"
                f"Diện tích: {float(p.area) if p.area is not None else ''} m2. "
                f"Giá: {float(p.price) if p.price is not None else ''} VND.\n"
            )

            metadatas.append({
                "post_id": pid,
                "is_deleted": 0,  # để filter khi search
                "price": float(p.price) if p.price is not None else 0.0,
                "area": float(p.area) if p.area is not None else 0.0,
                "district": district or "",
                "city": city or "",
                "category_id": int(p.category_id) if p.category_id is not None else 0,
                "post_type_id": int(p.post_type_id) if p.post_type_id is not None else 0,
            })

        # (C) Embed theo batch + upsert theo batch
        total = 0
        for i in range(0, len(docs), BATCH_SIZE):
            batch_docs = docs[i:i+BATCH_SIZE]
            batch_ids = ids[i:i+BATCH_SIZE]
            batch_meta = metadatas[i:i+BATCH_SIZE]

            emb_resp = client.embeddings.create(
                model="text-embedding-3-large",
                input=batch_docs,
            )
            vectors = [item.embedding for item in emb_resp.data]

            collection.upsert(
                ids=batch_ids,
                embeddings=vectors,
                metadatas=batch_meta,
                documents=batch_docs,
            )
            total += len(batch_ids)

        self.stdout.write(self.style.SUCCESS(f"Đã sync {total} Post sang Chroma"))
