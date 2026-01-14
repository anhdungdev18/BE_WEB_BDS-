from typing import Optional, Dict, Any
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

    return Notification.objects.create(
        user_id=user_id,
        actor_id=actor_id,
        type=type,
        title=title,
        content=content,
        target_type=target_type,
        target_id=target_id,
        extra=extra,
    )
