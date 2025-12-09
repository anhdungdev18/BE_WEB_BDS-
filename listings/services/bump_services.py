# listings/services/bump_services.py

from datetime import timedelta

from django.utils import timezone
from django.db import transaction

from listings.models import Post
from accounts.services.membership_services import get_active_membership


def get_daily_bump_limit(membership) -> int:
    """
    Xác định số lượt bump tối đa / ngày theo gói VIP.
    Ví dụ:
      - AGENT_1M: 10 lượt/ngày
      - AGENT_3M: 20 lượt/ngày
      - default: 10
    """
    if not membership or not membership.plan:
        return 0

    code = (membership.plan.code or "").upper()

    if code == "AGENT_3M":
        return 20
    if code == "AGENT_1M":
        return 10

    # mặc định nếu sau này có gói khác
    return 10


@transaction.atomic
def bump_post_for_request(post: Post, user):
    """
    Logic bump tin cho 1 bài đăng, dựa trên user đang đăng nhập.

    Điều kiện:
      - user phải là owner của post
      - user phải có VIP còn hiệu lực (UserMembership.is_active)
      - không vượt quá số lượt bump/ngày theo gói
    """

    # 1) Check owner
    user_id_str = str(user.id)
    if str(post.owner_id) != user_id_str:
        return {
            "ok": 0,
            "error": "NOT_OWNER",
            "message": "Bạn không phải chủ của bài đăng này.",
        }

    # 2) Check membership còn hiệu lực
    membership = get_active_membership(user)
    if not membership:
        return {
            "ok": 0,
            "error": "NO_ACTIVE_MEMBERSHIP",
            "message": "Tài khoản của bạn chưa có VIP hoặc đã hết hạn, không thể đẩy tin.",
        }

    # 3) Reset counter nếu sang ngày mới
    today = timezone.localdate()
    if membership.last_bump_date != today:
        membership.last_bump_date = today
        membership.bumps_used_today = 0

    # 4) Kiểm tra hạn mức theo gói
    daily_limit = get_daily_bump_limit(membership)
    if daily_limit <= 0:
        return {
            "ok": 0,
            "error": "NO_BUMP_ALLOWED",
            "message": "Gói VIP hiện tại không hỗ trợ đẩy tin.",
        }

    if membership.bumps_used_today >= daily_limit:
        return {
            "ok": 0,
            "error": "MAX_DAILY_BUMP_REACHED",
            "message": f"Bạn đã dùng hết {daily_limit} lượt đẩy tin hôm nay.",
        }

    # 5) Thực hiện bump: cập nhật bumped_at
    now = timezone.now()
    post.bumped_at = now
    post.save(update_fields=["bumped_at"])

    # 6) Tăng counter
    membership.bumps_used_today += 1
    membership.last_bump_date = today
    membership.save(update_fields=["bumps_used_today", "last_bump_date"])

    return {
        "ok": 1,
        "message": "BUMP_SUCCESS",
        "post_id": post.id,
        "bumped_at": now.isoformat(),
        "bumps_used_today": membership.bumps_used_today,
        "daily_limit": daily_limit,
    }
