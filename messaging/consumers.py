from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import json
from .models import ChatMessage

from django.contrib.auth.models import AnonymousUser

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Lấy user từ scope (JWT middleware đã gán)
        user = self.scope.get("user", None)

        # Nếu chưa đăng nhập hoặc token sai -> từ chối kết nối
        if not user or isinstance(user, AnonymousUser) or not user.is_authenticated:
            await self.close()
            return

        self.user = user
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.group = f"room_{self.room_id}"

        # Join group room_<room_id>
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        # Rời group
        await self.channel_layer.group_discard(self.group, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        """
        FE gửi JSON dạng:
        {
          "type": "chat.message",
          "text": "Nội dung tin nhắn"
        }

        ✅ KHÔNG còn cho FE gửi sender_id nữa.
        sender_id sẽ lấy từ self.user.id
        """
        try:
            data = json.loads(text_data or "{}")
        except json.JSONDecodeError:
            return

        if data.get("type") != "chat.message":
            return

        text = data.get("text", "").strip()
        if not text:
            return  # không lưu tin nhắn rỗng

        sender = self.user
        sender_id = sender.id

        # Lưu DB
        msg = await self._save(self.room_id, sender_id, text)

        # Payload gửi lại cho mọi người trong room
        payload = {
            "event": "message",
            "id": str(msg["id"]),
            "room": self.room_id,
            "sender_id": sender_id,
            "sender_name": getattr(sender, "username", "") or getattr(sender, "email", ""),
            "text": text,
            "created_at": msg["created_at"],
        }

        await self.channel_layer.group_send(
            self.group,
            {
                "type": "chat.msg",  # sẽ gọi chat_msg()
                "data": payload,
            },
        )

    async def chat_msg(self, event):
        """
        Handler để gửi payload xuống client.
        """
        await self.send(text_data=json.dumps(event["data"]))

    @database_sync_to_async
    def _save(self, room_id, sender_id, text):
        m = ChatMessage.objects.create(
            room_id=room_id,
            sender_id=sender_id,
            text=text,
        )
        return {
            "id": m.id,
            "created_at": m.created_at.isoformat(),
        }