# accounts/urls.py

from django.urls import path

from accounts.views import auth_views, test_views
from accounts.views.api_profile import (
    MeProfileAPIView,
    ChangePasswordAPIView,
)
from accounts.views.api_admin_users import (
    AdminUserListAPIView,
    AdminUserDetailAPIView,
    AdminResetPasswordAPIView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenBlacklistView,
)
from accounts.views.api_public_profile import PublicUserProfileAPIView
from accounts.views.api_google_login import GoogleLoginAPIView
from django.urls import path
from accounts.views.membership import (
    MembershipUpgradeInitAPIView,
    MembershipOrderMarkPaidAPIView,
    MembershipOrderListAPIView,
)
app_name = "accounts"

urlpatterns = [
    # ================== AUTH CŨ (GIỮ NGUYÊN) ==================
    path("signup/", auth_views.signup, name="signup"),
    path("login/",  auth_views.login,  name="login"),
    path("logout/", auth_views.logout, name="logout"),

    path("logout-test/", test_views.logout_test_page, name="logout-test"),

    # ================== PROFILE (USER) ==================
    # GET /api/accounts/me/profile/        -> xem hồ sơ chính mình
    # PUT /api/accounts/me/profile/        -> cập nhật hồ sơ chính mình
    path("profile", MeProfileAPIView.as_view(), name="me-profile"),
    path("profile/update", MeProfileAPIView.as_view(), name="me-profile-update"),

    # POST /api/accounts/password/change   -> đổi mật khẩu chính mình
    path("password/change", ChangePasswordAPIView.as_view(), name="me-change-password"),

    # ================== USERS (ADMIN) ==================
    # GET /api/accounts/users              -> danh sách user (admin)
    path("users", AdminUserListAPIView.as_view(), name="admin-user-list"),

    # (tuỳ huynh có xài thì dùng thêm 2 route dưới)
    # GET/PUT /api/accounts/admin/users/<user_id>/profile/
    path(
        "admin/users/<str:user_id>/profile/",
        AdminUserDetailAPIView.as_view(),
        name="admin-user-profile",
    ),
    # Refresh access token
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Blacklist refresh token (dùng cho logout)
    path("api/token/blacklist/", TokenBlacklistView.as_view(), name="token_blacklist"),

    # Nếu muốn giữ đường dẫn gốc luôn:
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    
    # POST /api/accounts/admin/users/<user_id>/reset-password/
    path(
        "admin/users/<str:user_id>/reset-password/",
        AdminResetPasswordAPIView.as_view(),
        name="admin-reset-password",
    ),
    path(
        "users/<str:user_id>/public-profile/",
        PublicUserProfileAPIView.as_view(),
        name="public-user-profile",
    ),

    # ================== GOOGLE LOGIN ==================
    path(
        "google-login/",
        GoogleLoginAPIView.as_view(),
        name="google-login",
    ),
    # ================== MEMBERSHIP ==================
    path(
        "membership/upgrade/init/",
        MembershipUpgradeInitAPIView.as_view(),
        name="membership-upgrade-init",
    ),
    path(
        "membership/orders/mark-paid/",
        MembershipOrderMarkPaidAPIView.as_view(),
        name="membership-order-mark-paid",
    ),
    path(
        "membership/orders/",
        MembershipOrderListAPIView.as_view(),
        name="membership-order-list",
    ),
]
