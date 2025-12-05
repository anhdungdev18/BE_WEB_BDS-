from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import json
from .models import ChatMessage

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.group = f"room_{self.room_id}"
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data or "{}")
        if data.get("type") == "chat.message":
            sender_id = data.get("sender_id")
            text = data.get("text", "")
            msg = await self._save(self.room_id, sender_id, text)
            payload = {
                "event":"message","id":str(msg["id"]),"room":self.room_id,
                "sender_id":sender_id,"text":text,"created_at":msg["created_at"]
            }
            await self.channel_layer.group_send(self.group, {"type":"chat.msg","data":payload})

    async def chat_msg(self, event):
        await self.send(text_data=json.dumps(event["data"]))

    @database_sync_to_async
    def _save(self, room_id, sender_id, text):
        m = ChatMessage.objects.create(room_id=room_id, sender_id=sender_id, text=text)
        return {"id": m.id, "created_at": m.created_at.isoformat()}
