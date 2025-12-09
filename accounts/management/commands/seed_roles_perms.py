# accounts/management/commands/seed_roles_perms.py

from django.core.management.base import BaseCommand

from accounts.models.role import Role
from accounts.models.permission import Permission
from accounts.models.role_permission import RolePermission


ROLE_DEFS = [
    ("SUPER_ADMIN", "Quản trị hệ thống, toàn quyền"),
    ("STAFF",       "Nhân viên vận hành, duyệt tin"),
    ("AGENT",       "Môi giới / chủ tin"),
    ("MEMBER",      "Người dùng thường"),
]

PERM_DEFS = [
    # code,                 ten_quyen,                              mo_ta
    ("post.create",          "Tạo bài đăng",                         "Cho phép tạo bài đăng mới"),
    ("post.update_own",      "Sửa bài của chính mình",               "Chỉ sửa bài do user tạo"),
    ("post.delete_soft_own", "Xóa mềm bài của chính mình",           "Ẩn bài, không xóa khỏi DB"),
    ("post.view_all",        "Xem tất cả bài đăng",                  "Bao gồm bài nháp, chờ duyệt"),
    ("post.approve",         "Duyệt bài đăng",                       "Duyệt cho bài hiển thị"),
    ("post.reject",          "Từ chối bài đăng",                     "Từ chối bài vi phạm"),

    # 🔥 Thêm các quyền liên quan VIP / BUMP / AUTO APPROVE
    ("post.create_vip",      "Tạo / nâng cấp bài VIP",               "Cho phép đánh dấu / nâng cấp tin thành VIP"),
    ("post.bump",            "Đẩy tin / bump tin",                   "Cho phép đẩy bài đăng lên trên danh sách"),
    ("post.auto_approve",    "Tự động duyệt bài đăng",               "Cho phép bài được duyệt tự động khi tạo"),

    ("user.view",            "Xem danh sách người dùng",             "Dùng cho admin/staff"),
    ("user.manage",          "Quản lý người dùng",                   "Khóa/mở khóa, gán role"),

    ("favorite.use",         "Lưu tin yêu thích",                    "Thêm/xóa tin vào danh sách yêu thích"),
    ("comment.create",       "Bình luận",                            "Tạo bình luận dưới bài đăng"),
    ("comment.manage",       "Quản lý bình luận",                    "Ẩn/xóa bình luận vi phạm"),

    ("report.view",          "Xem báo cáo",                          "Xem thống kê hệ thống"),
]

# mapping Role -> list permission code
ROLE_PERMS_MAP = {
    "SUPER_ADMIN": ["*"],  # full quyền, xử lý đặc biệt trong code

    "STAFF": [
        "post.view_all",
        "post.approve",
        "post.reject",
        "comment.manage",
        "user.view",
        "user.manage",
        "report.view",

        # Cho STAFF toàn quyền test & thao tác với VIP/bump
        "post.create",
        "post.create_vip",
        "post.bump",
        "post.auto_approve",
        "post.update_own",
        "post.delete_soft_own",
    ],

    "AGENT": [
        "post.create",
        "post.update_own",
        "post.delete_soft_own",

        # 💎 Chỉ AGENT (và STAFF/SUPER_ADMIN) có mấy quyền này
        "post.create_vip",
        "post.bump",
        "post.auto_approve",

        "favorite.use",
        "comment.create",
    ],

    "MEMBER": [
        "post.create",
        "post.update_own",
        "post.delete_soft_own",

        # ❌ Không có create_vip, bump, auto_approve
        "favorite.use",
        "comment.create",
    ],
}


class Command(BaseCommand):
    help = "Seed default roles and permissions for BDS system"

    def handle(self, *args, **options):
        # Tạo Permission
        perm_objs = {}
        for code, ten_quyen, mo_ta in PERM_DEFS:
            perm, created = Permission.objects.get_or_create(
                code=code,
                defaults={
                    "ten_quyen": ten_quyen,
                    "mo_ta": mo_ta,
                },
            )
            perm_objs[code] = perm

        # Tạo Role
        role_objs = {}
        for role_name, mo_ta in ROLE_DEFS:
            role, created = Role.objects.get_or_create(
                role_name=role_name,
                defaults={"mo_ta": mo_ta},
            )
            role_objs[role_name] = role

        # Gán Permission cho Role (trừ SUPER_ADMIN)
        for role_name, perm_codes in ROLE_PERMS_MAP.items():
            if "*" in perm_codes:
                continue

            role = role_objs[role_name]
            for code in perm_codes:
                perm = perm_objs[code]
                RolePermission.objects.get_or_create(
                    role=role,
                    permission=perm,
                )

        self.stdout.write(self.style.SUCCESS("Seed roles & permissions DONE."))
