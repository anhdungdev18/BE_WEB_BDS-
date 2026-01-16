# accounts/services/membership_services.py

from datetime import timedelta
from typing import Optional

from django.utils import timezone
from django.contrib.auth import get_user_model

from accounts.models import (
    MembershipPlan,
    MembershipOrder,
    UserMembership,
    Role,
    UserRole,
)

User = get_user_model()


def activate_membership_for_user(user, plan: MembershipPlan) -> UserMembership:
    """
    Kích hoạt hoặc gia hạn VIP cho user dựa trên MembershipPlan.

    - Nếu user CHƯA có UserMembership: tạo mới, hiệu lực từ bây giờ.
    - Nếu CÓ mà còn hạn: cộng thêm số ngày.
    - Nếu CÓ mà đã hết hạn: set lại từ bây giờ.

    Đồng thời gán role AGENT cho user (qua UserRole) để is_agent(request) dùng.
    """
    now = timezone.now()
    duration = timedelta(days=plan.duration_days)

    membership, created = UserMembership.objects.get_or_create(
        user=user,
        defaults={
            "plan": plan,
            "started_at": now,
            "expired_at": now + duration,
        },
    )

    if not created:
        # Cập nhật gói (ví dụ: từ 1 tháng lên 3 tháng)
        membership.plan = plan

        if membership.expired_at > now:
            # Đang còn hạn → nối thêm thời gian
            membership.expired_at = membership.expired_at + duration
            action_label = "Gia hạn VIP"
        else:
            # Hết hạn → reset từ bây giờ
            membership.started_at = now
            membership.expired_at = now + duration
            action_label = "Kích hoạt lại VIP"
    else:
        action_label = "Nâng cấp VIP"

    membership.save()

    # Gán role AGENT cho user (nếu chưa có)
    try:
        agent_role = Role.objects.get(role_name="AGENT")
        UserRole.objects.get_or_create(
            user=user,
            role=agent_role,
        )
    except Role.DoesNotExist:
        # Nếu chưa cấu hình role AGENT thì bỏ qua, không làm crash
        pass

    try:
        from notifications.services import create_notification

        create_notification(
            user_id=str(user.id),
            actor_id="system",
            type="membership",
            title=action_label,
            content=(
                f"{action_label} thành công. Gói: {getattr(plan, 'name', '')}. "
                f"Hiệu lực từ {membership.started_at} đến {membership.expired_at}."
            ),
            target_type="membership",
            target_id=str(plan.id) if getattr(plan, "id", None) else None,
            extra={
                "plan_code": getattr(plan, "code", None),
                "plan_name": getattr(plan, "name", None),
                "started_at": membership.started_at.isoformat(),
                "expired_at": membership.expired_at.isoformat(),
            },
        )
    except Exception:
        # Không làm fail luồng nâng cấp nếu thông báo lỗi.
        pass

    return membership


def get_active_membership(user) -> Optional[UserMembership]:
    """
    Lấy membership còn hiệu lực (expired_at > now), nếu không có thì trả None.

    Đồng thời:
    - Nếu membership tồn tại nhưng ĐÃ HẾT HẠN:
        + Trả None
        + Tắt role AGENT (is_active = False) trong UserRole (lazy cleanup).
    """
    mem = getattr(user, "membership", None)
    if not mem:
        # Không có bản ghi membership → không đụng tới role,
        # vì có thể admin set AGENT thủ công.
        return None

    now = timezone.now()
    if mem.expired_at <= now:
        # Hết hạn VIP → tắt AGENT cho user (nếu được gán bởi membership)
        UserRole.objects.filter(
            user=user,
            role__role_name="AGENT",
            is_active=True,
        ).update(is_active=False)
        return None

    return mem


def is_vip_account(user) -> bool:
    """
    Helper: user hiện tại có VIP đang hoạt động hay không.
    (Hàm này cũng sẽ tự động hạ role AGENT nếu membership đã hết hạn.)
    """
    return get_active_membership(user) is not None


def mark_order_paid_and_activate(order: MembershipOrder, bank_ref: str = "") -> MembershipOrder:
    """
    Dùng trong MembershipOrderMarkPaidAPIView:
    - Đánh dấu order = PAID
    - Ghi bank_ref, paid_at
    - Kích hoạt / gia hạn VIP cho user tương ứng
    """
    if order.status == MembershipOrder.Status.PAID:
        # Nếu đã PAID rồi thì thôi, trả lại order
        return order

    now = timezone.now()
    order.status = MembershipOrder.Status.PAID
    order.bank_ref = bank_ref
    order.paid_at = now
    order.save(update_fields=["status", "bank_ref", "paid_at"])

    # Kích hoạt / gia hạn VIP tài khoản
    activate_membership_for_user(order.user, order.plan)

    return order
