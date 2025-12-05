from django.views.generic import TemplateView 
from django.contrib import admin
from django.urls import path, include
from messaging.views import create_room, room_messages 
from django.views.generic import RedirectView
urlpatterns = [
    path('admin/', admin.site.urls),
    #path("", include("polls.urls")),
    path("", RedirectView.as_view(url="/admin/", permanent=False)),
    path("api/rooms", create_room),
    path("api/rooms/<uuid:room_id>/messages", room_messages),
    path("ws-test", TemplateView.as_view(template_name="ws_test.html")),

    # Accounts app 
    path("api/accounts/", include("accounts.urls")),
    # Listings app
    path("api/listings/", include("listings.urls")),
    # Engagement app 
    path("api/engagement/", include("engagement.urls", namespace="engagement")),
]
