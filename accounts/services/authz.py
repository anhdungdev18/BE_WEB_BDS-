# accounts/services/authz.py
from accounts.models import Role, Permission, UserRole
from django.utils import timezone

def get_user_role_names(user):
    """
    Trả về list tên role của user (ví dụ: ["SUPER_ADMIN", "STAFF"])
    """
    if not user.is_authenticated:
        return []

    return list(
        Role.objects.filter(
            role_users__user=user,
            role_users__is_active=True,
        ).values_list("role_name", flat=True)
    )


def is_super_admin(user) -> bool:
    """
    SUPER_ADMIN: full quyền, dùng cho các chức năng 'chỉ admin mới được làm'
    """
    return "SUPER_ADMIN" in get_user_role_names(user)


def is_admin_like(user) -> bool:
    """
    Nhóm vận hành nội dung (SUPER_ADMIN + STAFF)
    -> được phép duyệt/xóa/sửa bài của người khác
    """
    roles = set(get_user_role_names(user))
    return "SUPER_ADMIN" in roles or "STAFF" in roles


def user_has_perm(user, perm_code: str) -> bool:
    """
    Kiểm tra user có quyền perm_code hay không (ví dụ: 'post.create', 'post.update_own')
    """
    if not user.is_authenticated:
        return False

    # SUPER_ADMIN: full quyền
    if is_super_admin(user):
        return True

    return Permission.objects.filter(
        code=perm_code,
        roles__role_users__user=user,
        roles__role_users__is_active=True,
    ).exists()
def assign_role(user, role_name: str, granted_by=None) -> UserRole:
    """
    Gán (hoặc kích hoạt lại) một role cho user.
    Dùng khi:
      - Auto gán MEMBER lúc đăng ký
      - Nâng cấp lên AGENT sau khi thanh toán
    """
    role = Role.objects.get(role_name=role_name)

    ur, created = UserRole.objects.get_or_create(
        user=user,
        role=role,
        defaults={
            "assigned_at": timezone.now(),
            "is_active": True,
            "granted_by": granted_by,
        },
    )

    if not created:
        # Nếu đã có rồi thì bật lại is_active, cập nhật thời gian
        ur.is_active = True
        ur.assigned_at = timezone.now()
        if granted_by is not None:
            ur.granted_by = granted_by
        ur.save()

    return ur