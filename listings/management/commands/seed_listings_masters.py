from django.core.management.base import BaseCommand
from listings.models import PostType, Category, ApprovalStatus, PostStatus


class Command(BaseCommand):
    help = "Seed default data for PostType, Category, ApprovalStatus, PostStatus"

    def handle(self, *args, **options):
        # ========== POST TYPE ==========
        # PostType của huynh chỉ có field 'name'
        post_types = [
            "Bán",
            "Cho thuê",
        ]
        for name in post_types:
            obj, created = PostType.objects.get_or_create(name=name)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created PostType: {name}"))
            else:
                self.stdout.write(self.style.WARNING(f"PostType existed: {name}"))

        # ========== CATEGORY ==========
        # Category cũng chỉ có field 'name'
        categories = [
            "Căn hộ/Chung cư",
            "Nhà riêng",
            "Nhà mặt tiền",
            "Đất nền",
            "Văn phòng",
            "Mặt bằng kinh doanh",
        ]
        for name in categories:
            obj, created = Category.objects.get_or_create(name=name)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created Category: {name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Category existed: {name}"))

        # ========== APPROVAL STATUS ==========
        # Mấy model này trong admin có 'description', nên mình dùng luôn
        approval_statuses = [
            ("Pending",  "Chờ duyệt"),
            ("Approved", "Đã duyệt"),
            ("Rejected", "Bị từ chối"),
        ]
        for name, desc in approval_statuses:
            obj, created = ApprovalStatus.objects.get_or_create(
                name=name,
                defaults={"description": desc},
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created ApprovalStatus: {name}"))
            else:
                self.stdout.write(self.style.WARNING(f"ApprovalStatus existed: {name}"))

        # ========== POST STATUS ==========
        post_statuses = [
            ("Hidden",    "Ẩn, chưa hiển thị công khai"),
            ("Published", "Đang hiển thị công khai"),
            ("Archived",  "Đã lưu trữ, không còn hiển thị"),
        ]
        for name, desc in post_statuses:
            obj, created = PostStatus.objects.get_or_create(
                name=name,
                defaults={"description": desc},
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created PostStatus: {name}"))
            else:
                self.stdout.write(self.style.WARNING(f"PostStatus existed: {name}"))

        self.stdout.write(self.style.SUCCESS("✅ Seed listings masters DONE."))
