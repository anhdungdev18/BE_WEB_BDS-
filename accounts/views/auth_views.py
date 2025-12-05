# accounts/views/auth_views.py

from django.http import HttpResponse
from django.contrib.auth import get_user_model, authenticate
from ..services.authz import assign_role
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from rest_framework_simplejwt.tokens import RefreshToken

from ..serializers import RegisterSerializer, UserSerializer

User = get_user_model()


def index(request):
    return HttpResponse("Accounts API is up.")


# --- Signup ---
@api_view(["POST"])
@permission_classes([AllowAny])
def signup(request):
    """
    Đăng ký tài khoản mới.
    Sau khi tạo user xong -> tự động gán role MEMBER.
    """
    serializer = RegisterSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data

    # 1) Tạo user mới
    user = User.objects.create_user(
        username=data["username"],
        email=data["email"],
        password=data["password"],
    )

    # 2) Auto gán role MEMBER
    try:
        assign_role(user, "MEMBER", granted_by=None)
    except Exception:
        # Nếu quên seed role MEMBER thì không crash signup,
        # nhưng nên kiểm tra lại seed_roles_perms sau.
        pass

    # 3) Trả về info user
    return Response(
        UserSerializer(user).data,
        status=status.HTTP_201_CREATED,
    )



# --- Login (JWT, có thể dùng username hoặc email) ---
@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    """
    Đăng nhập bằng:
    - identifier  (username hoặc email), hoặc
    - username, hoặc
    - email
    + password

    Trả về:
    - user: thông tin người dùng
    - access: JWT access token
    - refresh: JWT refresh token
    """
    identifier = (
        request.data.get("identifier")
        or request.data.get("username")
        or request.data.get("email")
    )
    password = request.data.get("password")

    if not identifier or not password:
        return Response(
            {"error": "Tài khoản (username/email) và mật khẩu bắt buộc"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Nếu có '@' thì coi là email, không thì coi là username
    if "@" in identifier:
        try:
            user_obj = User.objects.get(email=identifier)
            username = user_obj.username
        except User.DoesNotExist:
            return Response(
                {"error": "Email hoặc mật khẩu không đúng"},
                status=status.HTTP_400_BAD_REQUEST,
            )
    else:
        username = identifier

    user = authenticate(request, username=username, password=password)
    if user is None:
        return Response(
            {"error": "Tài khoản hoặc mật khẩu không đúng"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not user.is_active:
        return Response(
            {"error": "Tài khoản đã bị khóa"},
            status=status.HTTP_403_FORBIDDEN,
        )

    # ✅ Tạo JWT tokens
    refresh = RefreshToken.for_user(user)
    access = refresh.access_token

    return Response(
        {
            "user": UserSerializer(user).data,
            "access": str(access),
            "refresh": str(refresh),
        },
        status=status.HTTP_200_OK,
    )


# --- Logout (blacklist refresh token) ---
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Logout theo JWT:
    - FE gửi refresh token lên (body: { "refresh": "<token>" }).
    - BE blacklist refresh token này (không dùng được nữa).
    """
    refresh_token = request.data.get("refresh")
    if not refresh_token:
        return Response(
            {"detail": "Thiếu refresh token."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        token = RefreshToken(refresh_token)
        token.blacklist()  # cần 'rest_framework_simplejwt.token_blacklist' + migrate
    except Exception:
        return Response(
            {"detail": "Refresh token không hợp lệ."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(
        {"detail": "Logout thành công. Refresh token đã bị thu hồi."},
        status=status.HTTP_200_OK,
    )
