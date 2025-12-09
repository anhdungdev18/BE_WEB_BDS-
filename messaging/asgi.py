import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter

from messaging.routing import websocket_urlpatterns
from messaging.jwt_middleware import JWTAuthMiddlewareStack  # 👈 import middleware mới

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")

django_app = get_asgi_application()

application = ProtocolTypeRouter(
    {
        "http": django_app,
        "websocket": JWTAuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        ),
    }
)
