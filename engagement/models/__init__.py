from .favorite import UserFavorite
from .rating import PostRating
from .comment import PostComment
# nếu có view.py:
from .view import PostView

__all__ = [
    "UserFavorite",
    "PostRating",
    "PostComment",
    "PostView",
]
