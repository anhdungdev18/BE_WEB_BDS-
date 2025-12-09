
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from django.contrib.auth import get_user_model

from .models import ChatRoom, ChatMessage

User = get_user_model()


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_room(request):
    """
    POST /api/rooms
    {
      "seller_id": "<id>",
      "listing_id": "<post_id>" (optional)
    }

    buyer = request.user (người đang đăng nhập)
    """
    buyer = request.user
    seller_id = request.data.get("seller_id")
    listing_id = request.data.get("listing_id")  # hoặc "listing" nếu đổi sang FK

    if not seller_id:
        return Response({"detail": "seller_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        seller = User.objects.get(id=seller_id)
    except User.DoesNotExist:
        return Response({"detail": "Seller not found"}, status=status.HTTP_404_NOT_FOUND)

    # Không tự chat với chính mình
    if buyer.id == seller.id:
        return Response({"detail": "Không thể tạo phòng với chính mình"}, status=status.HTTP_400_BAD_REQUEST)

    room, created = ChatRoom.objects.get_or_create(
        buyer=buyer,
        seller=seller,
        listing_id=listing_id,
    )

    return Response(
        {
            "room_id": str(room.id),
            "created": created,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def room_messages(request, room_id):
    """
    GET /api/rooms/<room_id>/messages
    -> trả tối đa 50 tin nhắn mới nhất trong room

    Chỉ cho phép nếu request.user là buyer hoặc seller của room.
    """
    try:
        room = ChatRoom.objects.get(id=room_id)
    except ChatRoom.DoesNotExist:
        return Response({"detail": "Room not found"}, status=status.HTTP_404_NOT_FOUND)

    user = request.user
    if user.id not in [room.buyer_id, room.seller_id]:
        return Response({"detail": "Bạn không có quyền xem phòng này"}, status=status.HTTP_403_FORBIDDEN)

    qs = ChatMessage.objects.filter(room=room).order_by("-created_at")[:50]
    # nếu muốn mới nhất lên đầu: sau khi list thì reverse lại
    messages = [
        {
            "id": str(m.id),
            "sender_id": m.sender_id,
            "text": m.text,
            "created_at": m.created_at.isoformat(),
        }
        for m in reversed(list(qs))  # đảo lại để cũ -> mới
    ]

    return Response({"messages": messages}, status=status.HTTP_200_OK)
