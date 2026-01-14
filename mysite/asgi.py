# mysite/asgi.py
import os
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")

import django
django.setup()  # <-- setup DJANGO trước khi import app khác

import messaging.routing  # <-- import sau khi setup
from messaging.jwt_middleware import JWTAuthMiddlewareStack  # <-- import sau khi setup

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": JWTAuthMiddlewareStack(
        URLRouter(messaging.routing.websocket_urlpatterns)
    ),
})
