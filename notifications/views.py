from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from .models import Notification
from .serializers import NotificationSerializer, NotificationReadSerializer


class NotificationListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = Notification.objects.filter(user=request.user).order_by("-created_at")[:200]
        data = NotificationSerializer(qs, many=True).data
        return Response({"items": data}, status=status.HTTP_200_OK)


class NotificationUnreadCountAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({"unread": count}, status=status.HTTP_200_OK)


class NotificationMarkReadAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = NotificationReadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        ids = serializer.validated_data.get("ids") or []
        mark_all = serializer.validated_data.get("mark_all", False)

        if mark_all:
            Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
            return Response({"ok": True, "updated": "all"}, status=status.HTTP_200_OK)

        if not ids:
            return Response({"detail": "ids or mark_all is required"}, status=status.HTTP_400_BAD_REQUEST)

        updated = Notification.objects.filter(user=request.user, id__in=ids).update(is_read=True)
        return Response({"ok": True, "updated": updated}, status=status.HTTP_200_OK)
