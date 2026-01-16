# listings/management/commands/process_bump_schedules.py

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from listings.models import PostBumpSchedule
from listings.services.bump_services import bump_post_for_request
from accounts.services.membership_services import get_active_membership
from notifications.services import create_notification

User = get_user_model()


def _get_tz(tz_name: str):
    try:
        return ZoneInfo(tz_name)
    except Exception:
        return timezone.get_default_timezone()


def _next_day_run_at(run_time, tz, from_dt):
    local_now = timezone.localtime(from_dt, tz)
    next_date = local_now.date() + timedelta(days=1)
    return datetime.combine(next_date, run_time, tzinfo=tz)


class Command(BaseCommand):
    help = "Process daily post bump schedules."

    def handle(self, *args, **options):
        processed = 0
        now = timezone.now()

        while True:
            with transaction.atomic():
                schedules = (
                    PostBumpSchedule.objects.select_for_update(skip_locked=True)
                    .select_related("post")
                    .filter(is_active=True, next_run_at__lte=now)
                    .order_by("next_run_at")[:100]
                )
                if not schedules:
                    break

                for schedule in schedules:
                    self._process_schedule(schedule, now)
                    processed += 1

            now = timezone.now()

        self.stdout.write(f"Processed {processed} schedule(s).")

    def _pause_schedule(self, schedule, reason):
        schedule.is_active = False
        schedule.status = PostBumpSchedule.STATUS_PAUSED
        schedule.fail_reason = reason
        schedule.next_run_at = None
        schedule.save(update_fields=["is_active", "status", "fail_reason", "next_run_at"])

    def _reschedule_next_day(self, schedule, tz, reason=None):
        schedule.fail_reason = reason
        schedule.next_run_at = _next_day_run_at(schedule.run_time, tz, timezone.now())
        schedule.save(update_fields=["fail_reason", "next_run_at"])

    def _process_schedule(self, schedule, now):
        post = schedule.post
        if not post or getattr(post, "is_deleted", False):
            self._pause_schedule(schedule, "POST_NOT_FOUND")
            return

        owner_id = str(schedule.owner_id)
        if str(post.owner_id) != owner_id:
            self._pause_schedule(schedule, "NOT_OWNER")
            return

        user = User.objects.filter(id=owner_id).first()
        if not user:
            self._pause_schedule(schedule, "USER_NOT_FOUND")
            return

        membership = get_active_membership(user)
        if not membership:
            self._pause_schedule(schedule, "NO_ACTIVE_MEMBERSHIP")
            return

        approval_name = getattr(post.approval_status, "name", None)
        if approval_name and approval_name.lower() != "approved":
            self._pause_schedule(schedule, "NOT_APPROVED")
            return

        post_status_name = getattr(post.post_status, "name", None)
        if post_status_name and post_status_name.lower() != "published":
            self._pause_schedule(schedule, "NOT_PUBLISHED")
            return

        result = bump_post_for_request(post, user)
        if not isinstance(result, dict) or result.get("ok") != 1:
            error = result.get("error") if isinstance(result, dict) else "UNKNOWN_ERROR"
            tz = _get_tz(schedule.timezone)
            if error in ("MAX_DAILY_BUMP_REACHED", "POST_DAILY_BUMP_REACHED"):
                self._reschedule_next_day(schedule, tz, error)
                return
            if error in ("NO_ACTIVE_MEMBERSHIP", "NO_BUMP_ALLOWED"):
                self._pause_schedule(schedule, error)
                return
            if error in ("NOT_APPROVED", "NOT_PUBLISHED", "NOT_OWNER"):
                self._pause_schedule(schedule, error)
                return
            self._reschedule_next_day(schedule, tz, error)
            return

        tz = _get_tz(schedule.timezone)
        schedule.last_run_at = now
        schedule.fail_reason = None
        schedule.status = PostBumpSchedule.STATUS_ACTIVE
        schedule.next_run_at = _next_day_run_at(schedule.run_time, tz, now)
        schedule.save(update_fields=["last_run_at", "fail_reason", "status", "next_run_at"])

        local_now = timezone.localtime(now, tz)
        title = "Đẩy tin thành công"
        content = f'Bài đăng "{post.title}" đã được đẩy lúc {local_now.strftime("%H:%M")}.'
        create_notification(
            user_id=owner_id,
            actor_id="system",
            type="post_bump",
            title=title,
            content=content,
            target_type="post",
            target_id=str(post.id),
            extra={
                "schedule_id": schedule.id,
                "bumped_at": now.isoformat(),
            },
        )
