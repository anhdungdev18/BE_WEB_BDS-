# listings/urls.py
from django.urls import path

from listings.views.post_api import (
    PostListCreateView,
    PostDetailView,
    PostStatusChangeView,
    OwnerPostListView,
    PostBumpView,
    MyPostListView,
    OwnerPostStatusChangeView,

)
from listings.views.bump_schedule_api import (
    PostBumpScheduleCreateView,
    MyBumpScheduleListView,
    BumpScheduleDetailView,
)
from .views.category import CategoryListAPIView
from .views.post_type import PostTypeListAPIView

urlpatterns = [
    # /api/listings/posts
    path("posts", PostListCreateView.as_view(), name="post-list-create"),
    # /api/listings/posts/<id>
    path("posts/<str:post_id>", PostDetailView.as_view(), name="post-detail"),
    # /api/listings/posts/<id>/status
    path(
        "posts/<str:post_id>/status",
        PostStatusChangeView.as_view(),
        name="post-status-change",
    ),
    path(
        "owner-posts/",
        OwnerPostListView.as_view(),
        name="owner-posts",
    ),
    path("posts/<str:post_id>/bump", PostBumpView.as_view(), name="post-bump"),
    path(
        "posts/<str:post_id>/bump-schedule",
        PostBumpScheduleCreateView.as_view(),
        name="post-bump-schedule",
    ),
    path("categories/", CategoryListAPIView.as_view(), name="category-list"),
    path("post-types/", PostTypeListAPIView.as_view(), name="posttype-list"),
    path("me/posts", MyPostListView.as_view(), name="my-posts"),
    path("me/bump-schedules", MyBumpScheduleListView.as_view(), name="my-bump-schedules"),
    path(
        "bump-schedules/<int:schedule_id>",
        BumpScheduleDetailView.as_view(),
        name="bump-schedule-detail",
    ),
    
    path(
        "posts/<str:post_id>/owner-status",
        OwnerPostStatusChangeView.as_view(),
        name="post-owner-status-change",
    )

]
