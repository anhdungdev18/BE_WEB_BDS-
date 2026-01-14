from django.urls import path
from .views import create_room, room_messages, my_rooms 

urlpatterns = [
    path("rooms/", create_room, name="create-room"),
    path("rooms/my/", my_rooms, name="my-rooms"),   
    path("rooms/<uuid:room_id>/messages/", room_messages, name="room-messages"),
]
