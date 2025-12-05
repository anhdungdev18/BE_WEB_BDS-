# listings/urls.py
from django.urls import path

from listings.views.post_api import (
    PostListCreateView,
    PostDetailView,
    PostStatusChangeView,
    OwnerPostListView,
)

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
]
