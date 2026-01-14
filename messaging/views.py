from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from django.contrib.auth import get_user_model
from django.db.models import Q
from .models import ChatRoom, ChatMessage
from notifications.services import create_notification

User = get_user_model()


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_room(request):
    buyer = request.user
    seller_id = request.data.get("seller_id")
    listing_id = request.data.get("listing_id")

    if not seller_id:
        return Response({"detail": "seller_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        seller = User.objects.get(id=seller_id)
    except User.DoesNotExist:
        return Response({"detail": "Seller not found"}, status=status.HTTP_404_NOT_FOUND)

    if buyer.id == seller.id:
        return Response({"detail": "Không thể tạo phòng với chính mình"}, status=status.HTTP_400_BAD_REQUEST)

    room, created = ChatRoom.objects.get_or_create(
        buyer=buyer,
        seller=seller,
        listing_id=listing_id,
    )

    return Response({"room_id": str(room.id), "created": created}, status=status.HTTP_200_OK)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def room_messages(request, room_id):
    """
    GET  /api/rooms/<room_id>/messages/  -> trả 50 tin nhắn mới nhất
    POST /api/rooms/<room_id>/messages/  -> gửi tin { "text": "..." }
    """
    try:
        room = ChatRoom.objects.get(id=room_id)
    except ChatRoom.DoesNotExist:
        return Response({"detail": "Room not found"}, status=status.HTTP_404_NOT_FOUND)

    user = request.user
    if user.id not in [room.buyer_id, room.seller_id]:
        return Response({"detail": "Bạn không có quyền xem phòng này"}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "POST":
        text = (request.data.get("text") or "").strip()
        if not text:
            return Response({"detail": "text is required"}, status=status.HTTP_400_BAD_REQUEST)

        m = ChatMessage.objects.create(room=room, sender=user, text=text)
        other_user_id = room.seller_id if user.id == room.buyer_id else room.buyer_id
        create_notification(
            user_id=other_user_id,
            actor_id=user.id,
            type="message",
            title="Tin nhắn mới",
            content=text[:200],
            target_type="room",
            target_id=str(room.id),
            extra={"message_id": str(m.id)},
        )
        return Response(
            {
                "id": str(m.id),
                "sender_id": m.sender_id,
                "text": m.text,
                "created_at": m.created_at.isoformat(),
            },
            status=status.HTTP_201_CREATED,
        )

    qs = ChatMessage.objects.filter(room=room).order_by("-created_at")[:50]
    messages = [
        {
            "id": str(m.id),
            "sender_id": m.sender_id,
            "text": m.text,
            "created_at": m.created_at.isoformat(),
        }
        for m in reversed(list(qs))
    ]
    return Response({"messages": messages}, status=status.HTTP_200_OK)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_rooms(request):
    user = request.user
    qs = ChatRoom.objects.filter(Q(buyer=user) | Q(seller=user)).order_by("-created_at")

    rooms = [
        {
            "room_id": str(r.id),
            "buyer_id": r.buyer_id,
            "seller_id": r.seller_id,
            "listing_id": str(r.listing_id) if r.listing_id else None,
            "created_at": r.created_at.isoformat() if hasattr(r, "created_at") else None,
        }
        for r in qs
    ]
    return Response({"rooms": rooms}, status=status.HTTP_200_OK)
