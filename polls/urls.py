from django.urls import path
from .views import auth_views, post_views, category_views, posttype_views
from rest_framework_simplejwt.views import TokenRefreshView, TokenBlacklistView, TokenObtainPairView
urlpatterns = [
    path('', auth_views.index, name='index'),

    # Auth
    path('signup/', auth_views.signup),
    path('login/', auth_views.login),
    path('logout/', auth_views.logout),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    # Post Type
    path('posttypes/', posttype_views.posttype_list),

    # Category
    path('categories/', category_views.category_list),

    # Post
    path('posts/', post_views.post_list),
    path('posts/<int:pk>/', post_views.post_detail),

]
