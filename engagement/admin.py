from django.contrib import admin
from .models import PostComment, UserFavorite, PostRating


@admin.register(PostComment)
class PostCommentAdmin(admin.ModelAdmin):
    # Dùng id thô (user_id, post_id)
    list_display = ("id", "post_id", "user_id", "parent_id", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("post_id", "user_id", "content")
    ordering = ("-created_at",)


@admin.register(UserFavorite)
class UserFavoriteAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "post_id", "created_at")
    search_fields = ("user_id", "post_id")
    ordering = ("-created_at",)


@admin.register(PostRating)
class PostRatingAdmin(admin.ModelAdmin):
    list_display = ("id", "post_id", "user_id", "score", "created_at")
    list_filter = ("score",)
    search_fields = ("user_id", "post_id")
    ordering = ("-created_at",)
