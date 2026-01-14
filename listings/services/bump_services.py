# listings/services/bump_services.py

from datetime import timedelta

from django.utils import timezone
from django.db import transaction

from listings.models import Post, PostBumpLog
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
            "daily_limit": 0,
            "bumps_used_today": 0,
            "remaining_today": 0,
            "post_daily_limit": 2,
            "post_bumps_used_today": 0,
            "post_remaining_today": 0,
        }

    # 2.1) Chỉ cho bump bài đã được duyệt và đang hiển thị
    approval_name = getattr(post.approval_status, "name", None)
    if approval_name and approval_name.lower() != "approved":
        return {
            "ok": 0,
            "error": "NOT_APPROVED",
            "message": "Bài đăng chưa được duyệt, không thể đẩy tin.",
        }

    post_status_name = getattr(post.post_status, "name", None)
    if post_status_name and post_status_name.lower() != "published":
        return {
            "ok": 0,
            "error": "NOT_PUBLISHED",
            "message": "Bài đăng chưa hiển thị, không thể đẩy tin.",
        }

    # 3) Reset counter nếu sang ngày mới
    today = timezone.localdate()
    if membership.last_bump_date != today:
        membership.last_bump_date = today
        membership.bumps_used_today = 0

    # 3.1) Giới hạn bump theo bài/ngày
    post_daily_limit = 2
    post_daily_count = PostBumpLog.objects.filter(
        post=post,
        created_at__date=today,
    ).count()
    if post_daily_count >= post_daily_limit:
        return {
            "ok": 0,
            "error": "POST_DAILY_BUMP_REACHED",
            "message": "Mỗi bài chỉ được đẩy tối đa 2 lần mỗi ngày.",
            "daily_limit": get_daily_bump_limit(membership),
            "bumps_used_today": membership.bumps_used_today,
            "remaining_today": max(get_daily_bump_limit(membership) - membership.bumps_used_today, 0),
            "post_daily_limit": post_daily_limit,
            "post_bumps_used_today": post_daily_count,
            "post_remaining_today": 0,
        }

    # 4) Kiểm tra hạn mức theo gói
    daily_limit = get_daily_bump_limit(membership)
    if daily_limit <= 0:
        return {
            "ok": 0,
            "error": "NO_BUMP_ALLOWED",
            "message": "Gói VIP hiện tại không hỗ trợ đẩy tin.",
            "daily_limit": daily_limit,
            "bumps_used_today": membership.bumps_used_today,
            "remaining_today": 0,
            "post_daily_limit": post_daily_limit,
            "post_bumps_used_today": post_daily_count,
            "post_remaining_today": max(post_daily_limit - post_daily_count, 0),
        }

    if membership.bumps_used_today >= daily_limit:
        return {
            "ok": 0,
            "error": "MAX_DAILY_BUMP_REACHED",
            "message": f"Bạn đã dùng hết {daily_limit} lượt đẩy tin hôm nay.",
            "daily_limit": daily_limit,
            "bumps_used_today": membership.bumps_used_today,
            "remaining_today": 0,
            "post_daily_limit": post_daily_limit,
            "post_bumps_used_today": post_daily_count,
            "post_remaining_today": max(post_daily_limit - post_daily_count, 0),
        }

    # 5) Thực hiện bump: cập nhật bumped_at
    now = timezone.now()
    post.bumped_at = now
    post.save(update_fields=["bumped_at"])

    # 6) Tăng counter
    membership.bumps_used_today += 1
    membership.last_bump_date = today
    membership.save(update_fields=["bumps_used_today", "last_bump_date"])

    # 7) Ghi log bump
    plan_code = (getattr(membership.plan, "code", "") or "").upper()
    PostBumpLog.objects.create(
        post=post,
        actor_id=user_id_str,
        is_agent="AGENT" in plan_code,
    )

    return {
        "ok": 1,
        "message": "BUMP_SUCCESS",
        "post_id": post.id,
        "bumped_at": now.isoformat(),
        "bumps_used_today": membership.bumps_used_today,
        "daily_limit": daily_limit,
        "remaining_today": max(daily_limit - membership.bumps_used_today, 0),
        "post_daily_limit": post_daily_limit,
        "post_bumps_used_today": post_daily_count + 1,
        "post_remaining_today": max(post_daily_limit - (post_daily_count + 1), 0),
    }
