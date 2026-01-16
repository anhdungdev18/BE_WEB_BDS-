# listings/views/bump_schedule_api.py

from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo

from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from listings.models import Post, PostBumpSchedule
from listings.services.auth_helpers import has_perm
from accounts.services.membership_services import get_active_membership


def _parse_run_time(value) -> time:
    if value is None or value == "":
        raise ValueError("run_time is required")
    if isinstance(value, time):
        return value

    raw = str(value).strip()
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(raw, fmt).time()
        except ValueError:
            continue
    raise ValueError("run_time must be HH:MM or HH:MM:SS")


def _get_tz(tz_name: str):
    try:
        return ZoneInfo(tz_name)
    except Exception:
        return timezone.get_default_timezone()


def _compute_next_run_at(run_time: time, tz):
    now = timezone.now()
    local_now = timezone.localtime(now, tz)
    candidate = datetime.combine(local_now.date(), run_time, tzinfo=tz)
    if candidate <= local_now:
        candidate = datetime.combine(local_now.date() + timedelta(days=1), run_time, tzinfo=tz)
    return candidate


def _serialize_schedule(schedule: PostBumpSchedule):
    return {
        "id": schedule.id,
        "post_id": str(schedule.post_id),
        "owner_id": schedule.owner_id,
        "run_time": schedule.run_time.isoformat(),
        "timezone": schedule.timezone,
        "is_active": schedule.is_active,
        "status": schedule.status,
        "last_run_at": schedule.last_run_at.isoformat() if schedule.last_run_at else None,
        "next_run_at": schedule.next_run_at.isoformat() if schedule.next_run_at else None,
        "fail_reason": schedule.fail_reason,
    }


class PostBumpScheduleCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, post_id: str, *args, **kwargs):
        if not has_perm(request, "post.bump"):
            return Response(
                {"detail": "Không có quyền đẩy tin (post.bump)"},
                status=status.HTTP_403_FORBIDDEN,
            )

        post = get_object_or_404(Post, pk=post_id, is_deleted=False)

        if str(post.owner_id) != str(request.user.id):
            return Response(
                {"ok": 0, "error": "NOT_OWNER", "message": "Bạn không phải chủ bài đăng."},
                status=status.HTTP_403_FORBIDDEN,
            )

        membership = get_active_membership(request.user)
        if not membership:
            return Response(
                {"ok": 0, "error": "NO_ACTIVE_MEMBERSHIP", "message": "Tài khoản chưa có VIP."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        approval_name = getattr(post.approval_status, "name", None)
        if approval_name and approval_name.lower() != "approved":
            return Response(
                {"ok": 0, "error": "NOT_APPROVED", "message": "Bài đăng chưa được duyệt."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        post_status_name = getattr(post.post_status, "name", None)
        if post_status_name and post_status_name.lower() != "published":
            return Response(
                {"ok": 0, "error": "NOT_PUBLISHED", "message": "Bài đăng chưa hiển thị."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            run_time = _parse_run_time(request.data.get("run_time"))
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        tz_name = request.data.get("timezone") or "Asia/Ho_Chi_Minh"
        tz = _get_tz(tz_name)
        next_run_at = _compute_next_run_at(run_time, tz)

        schedule, _ = PostBumpSchedule.objects.update_or_create(
            post=post,
            owner_id=str(request.user.id),
            defaults={
                "run_time": run_time,
                "timezone": tz_name,
                "is_active": True,
                "status": PostBumpSchedule.STATUS_ACTIVE,
                "next_run_at": next_run_at,
                "fail_reason": None,
            },
        )

        return Response(_serialize_schedule(schedule), status=status.HTTP_200_OK)


class MyBumpScheduleListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        qs = (
            PostBumpSchedule.objects.filter(owner_id=str(request.user.id))
            .order_by("next_run_at", "-created_at")
        )
        data = [_serialize_schedule(s) for s in qs]
        return Response({"results": data}, status=status.HTTP_200_OK)


class BumpScheduleDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, schedule_id: int, *args, **kwargs):
        schedule = get_object_or_404(
            PostBumpSchedule,
            pk=schedule_id,
            owner_id=str(request.user.id),
        )

        data = request.data or {}
        updated_fields = []

        if "run_time" in data:
            try:
                schedule.run_time = _parse_run_time(data.get("run_time"))
            except ValueError as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            updated_fields.append("run_time")

        if "timezone" in data:
            schedule.timezone = data.get("timezone") or schedule.timezone
            updated_fields.append("timezone")

        if "is_active" in data:
            schedule.is_active = bool(data.get("is_active"))
            schedule.status = (
                PostBumpSchedule.STATUS_ACTIVE
                if schedule.is_active
                else PostBumpSchedule.STATUS_PAUSED
            )
            updated_fields.extend(["is_active", "status"])

        tz = _get_tz(schedule.timezone)
        schedule.next_run_at = _compute_next_run_at(schedule.run_time, tz)
        schedule.fail_reason = None
        updated_fields.extend(["next_run_at", "fail_reason"])

        schedule.save(update_fields=list(set(updated_fields)))

        return Response(_serialize_schedule(schedule), status=status.HTTP_200_OK)

    def delete(self, request, schedule_id: int, *args, **kwargs):
        schedule = get_object_or_404(
            PostBumpSchedule,
            pk=schedule_id,
            owner_id=str(request.user.id),
        )
        schedule.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
