from rest_framework import serializers
from .models import UserFavorite, PostRating, PostComment, PostView


class UserFavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserFavorite
        fields = ["id", "user_id", "post_id", "created_at"]
        read_only_fields = ["id", "created_at", "user_id"]


class PostRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostRating
        fields = [
            "id",
            "user_id",
            "post_id",
            "score",
            "comment",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user_id", "created_at", "updated_at"]

    def validate_score(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Score phải từ 1 đến 5.")
        return value


class PostCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostComment
        fields = [
            "id",
            "user_id",
            "post_id",
            "parent",
            "content",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user_id", "status", "created_at", "updated_at"]


class PostViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostView
        fields = [
            "id",
            "user_id",
            "post_id",
            "session_id",
            "ip_address",
            "user_agent",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "user_id", "ip_address", "user_agent"]
