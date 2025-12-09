from django.urls import path
from .views import create_room, room_messages

urlpatterns = [
    path("rooms", create_room, name="create-room"),
    path("rooms/<uuid:room_id>/messages", room_messages, name="room-messages"),
]
