from django.views.generic import TemplateView 
from django.contrib import admin
from django.urls import path, include
from messaging.views import create_room, room_messages 
from django.views.generic import RedirectView
from accounts.views.password_reset_page import reset_password_page
from chatbot.api import ChatbotAPIView 
from django.http import JsonResponse
 
def ping(request):
    return JsonResponse({"ok": True, "where": "mysite.urls"})

urlpatterns = [
    path('admin/', admin.site.urls),
    path("ping/", ping),
    #path("", include("polls.urls")),
    path("", RedirectView.as_view(url="/admin/", permanent=False)),
    path("test/notifications/", TemplateView.as_view(template_name="notifications_test.html")),
    # Messaging app
    path("rooms/", include("messaging.urls")),
    path("api/", include("messaging.urls")),
    # Accounts app 
    path("api/accounts/", include("accounts.urls")),
    # Listings app
    path("api/listings/", include("listings.urls")),
    # Engagement app 
    path("api/engagement/", include("engagement.urls", namespace="engagement")),
    # Notifications app
    path("api/notifications/", include("notifications.urls")),
    # Chatbot app
    path("api/chatbot/", ChatbotAPIView.as_view(), name="chatbot"),
    path("reset-password/", reset_password_page, name="reset-password-page"),
]

