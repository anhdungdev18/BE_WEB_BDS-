
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from .models import ChatRoom, ChatMessage
import json

User = get_user_model()

@csrf_exempt
@require_POST
def create_room(request):
    data = json.loads(request.body.decode("utf-8"))
    buyer = User.objects.get(id=data["buyer_id"])
    seller = User.objects.get(id=data["seller_id"])
    room, _ = ChatRoom.objects.get_or_create(buyer=buyer, seller=seller, listing_id=data.get("listing_id"))
    return JsonResponse({"room_id": str(room.id)})

def room_messages(request, room_id):
    qs = ChatMessage.objects.filter(room_id=room_id).order_by("created_at")[:50]
    items = [{"id":str(m.id),"sender":m.sender_id,"text":m.text,"created_at":m.created_at.isoformat()} for m in qs]
    return JsonResponse({"messages": items})
