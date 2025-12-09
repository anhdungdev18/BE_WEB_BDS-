# messaging/jwt_middleware.py

import urllib.parse

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from django.conf import settings

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()


@database_sync_to_async
def get_user_from_token(token_str: str):
    """
    Decode JWT access token và trả về User tương ứng.
    Nếu token không hợp lệ -> AnonymousUser.
    """
    try:
        access = AccessToken(token_str)
        user_id = access.get("user_id")  # SimpleJWT claim mặc định là "user_id"
        if not user_id:
            return AnonymousUser()
        try:
            user = User.objects.get(id=user_id)
            if not user.is_active:
                return AnonymousUser()
            return user
        except User.DoesNotExist:
            return AnonymousUser()
    except Exception:
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """
    Middleware cho Channels:
    - Lấy token từ query string: ?token=<access_token>
    - Verify bằng SimpleJWT
    - Gán scope["user"]
    """

    async def __call__(self, scope, receive, send):
        # Lấy token từ query string
        query_string = scope.get("query_string", b"").decode()
        query_params = urllib.parse.parse_qs(query_string)
        token_list = query_params.get("token") or query_params.get("access") or []
        token = token_list[0] if token_list else None

        if token:
            scope["user"] = await get_user_from_token(token)
        else:
            scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)


def JWTAuthMiddlewareStack(inner):
    """
    Helper giống AuthMiddlewareStack, nhưng dùng JWTAuthMiddleware.
    """
    return JWTAuthMiddleware(inner)
