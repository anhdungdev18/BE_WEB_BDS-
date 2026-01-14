from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
import json


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user", None)
        if not user or isinstance(user, AnonymousUser) or not user.is_authenticated:
            await self.close()
            return

        self.user = user
        self.group = f"notif_{self.user.id}"

        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, "group"):
            await self.channel_layer.group_discard(self.group, self.channel_name)

    async def notify_message(self, event):
        await self.send(text_data=json.dumps(event.get("data", {})))
