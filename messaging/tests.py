from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from django.contrib.auth import get_user_model

from .models import ChatRoom, ChatMessage

User = get_user_model()


class MessagingViewsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.buyer = User.objects.create_user(
            username="buyer",
            email="buyer@example.com",
            password="pass1234",
        )
        self.seller = User.objects.create_user(
            username="seller",
            email="seller@example.com",
            password="pass1234",
        )

    def test_create_room_requires_seller_id(self):
        self.client.force_authenticate(self.buyer)
        response = self.client.post("/api/rooms/", {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_room_success_and_idempotent(self):
        self.client.force_authenticate(self.buyer)
        payload = {"seller_id": self.seller.id, "listing_id": "LIST123"}

        first = self.client.post("/api/rooms/", payload, format="json")
        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertTrue(first.data["created"])

        second = self.client.post("/api/rooms/", payload, format="json")
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertFalse(second.data["created"])
        self.assertEqual(first.data["room_id"], second.data["room_id"])

    def test_room_messages_post_and_get(self):
        room = ChatRoom.objects.create(
            buyer=self.buyer,
            seller=self.seller,
            listing_id="LIST123",
        )

        self.client.force_authenticate(self.buyer)
        post_resp = self.client.post(
            f"/api/rooms/{room.id}/messages/",
            {"text": "hello"},
            format="json",
        )
        self.assertEqual(post_resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ChatMessage.objects.filter(room=room).count(), 1)

        get_resp = self.client.get(f"/api/rooms/{room.id}/messages/")
        self.assertEqual(get_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(get_resp.data["messages"]), 1)
        self.assertEqual(get_resp.data["messages"][0]["text"], "hello")

    def test_my_rooms_returns_rooms(self):
        room = ChatRoom.objects.create(
            buyer=self.buyer,
            seller=self.seller,
            listing_id="LIST123",
        )
        self.client.force_authenticate(self.buyer)
        resp = self.client.get("/api/rooms/my/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        room_ids = [r["room_id"] for r in resp.data["rooms"]]
        self.assertIn(str(room.id), room_ids)
