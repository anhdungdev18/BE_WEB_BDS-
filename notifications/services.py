from typing import Optional, Dict, Any
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Notification


def create_notification(
    *,
    user_id: str,
    actor_id: str,
    type: str,
    title: str,
    content: Optional[str] = None,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
):
    if not user_id or not actor_id:
        return None
    if str(user_id) == str(actor_id):
        return None

    notif = Notification.objects.create(
        user_id=user_id,
        actor_id=actor_id,
        type=type,
        title=title,
        content=content,
        target_type=target_type,
        target_id=target_id,
        extra=extra,
    )

    channel_layer = get_channel_layer()
    if channel_layer is not None:
        payload = {
            "id": str(notif.id),
            "type": notif.type,
            "title": notif.title,
            "content": notif.content,
            "actor_id": notif.actor_id,
            "target_type": notif.target_type,
            "target_id": notif.target_id,
            "extra": notif.extra,
            "is_read": notif.is_read,
            "created_at": notif.created_at.isoformat(),
        }
        try:
            async_to_sync(channel_layer.group_send)(
                f"notif_{notif.user_id}",
                {"type": "notify.message", "data": payload},
            )
        except Exception:
            pass

    return notif
