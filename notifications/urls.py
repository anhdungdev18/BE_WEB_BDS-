from django.urls import path
from .views import (
    NotificationListAPIView,
    NotificationUnreadCountAPIView,
    NotificationMarkReadAPIView,
)

urlpatterns = [
    path("", NotificationListAPIView.as_view(), name="notification-list"),
    path("unread-count/", NotificationUnreadCountAPIView.as_view(), name="notification-unread"),
    path("mark-read/", NotificationMarkReadAPIView.as_view(), name="notification-mark-read"),
]
