# engagement/urls.py
from django.urls import path

from engagement.views.favorite_api import (
    FavoriteToggleAPIView,
    FavoriteMyListAPIView,
    FavoriteUsersByPostAPIView,
    FavoriteMeAPIView, FavoriteMyBatchAPIView
)
from engagement.views.rating_api import (
    RatingUpsertAPIView,
    RatingListByPostAPIView,
    RatingSummaryAPIView

)
from engagement.views.comment_api import (
    CommentCreateAPIView,
    CommentListByPostAPIView,
    CommentUsersByPostAPIView,
)
from engagement.views.view_api import (
    PostViewCreateAPIView,
    PostViewSummaryAPIView,
)
from engagement.views.batch_summary_api import PostSummaryBatchAPIView
app_name = "engagement"

urlpatterns = [
    # Favorites
    path("favorites/toggle/", FavoriteToggleAPIView.as_view(), name="favorite-toggle"),
    path("favorites/my/",     FavoriteMyListAPIView.as_view(), name="favorite-my"),
    path("favorites/users/",  FavoriteUsersByPostAPIView.as_view(), name="favorite-users"),

    # Ratings
    path("ratings/",      RatingUpsertAPIView.as_view(), name="rating-upsert"),
    path("ratings/list/", RatingListByPostAPIView.as_view(), name="rating-list"),

    # Comments
    path("comments/",       CommentCreateAPIView.as_view(),    name="comment-create"),
    path("comments/list/",  CommentListByPostAPIView.as_view(), name="comment-list"),
    path("comments/users/", CommentUsersByPostAPIView.as_view(), name="comment-users"),

    # Views
    path("views/",          PostViewCreateAPIView.as_view(),   name="post-view-create"),
    path("views/summary/",  PostViewSummaryAPIView.as_view(),  name="post-view-summary"),

    path("favorites/me/", FavoriteMeAPIView.as_view(), name="eng-favorite-me"),
    path("favorites/my/batch/", FavoriteMyBatchAPIView.as_view(), name="eng-favorite-my-batch"),

    path("ratings/summary/", RatingSummaryAPIView.as_view(), name="eng-rating-summary"),

    path("posts/summary/batch/", PostSummaryBatchAPIView.as_view(), name="eng-post-summary-batch"),
]
