# chatbot/models.py
from django.db import models
from django.conf import settings

class ChatSession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
    )
    session_id = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"ChatSession({self.session_id})"


class ChatTurn(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="turns")
    role = models.CharField(max_length=20, choices=[("user", "User"), ("assistant", "Assistant")])
    message = models.TextField()
    intent = models.CharField(max_length=50, null=True, blank=True)
    filters_json = models.JSONField(null=True, blank=True)
    retrieved_ids = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class SearchContext(models.Model):
    """Lưu filter tìm kiếm gần nhất của session để hỗ trợ follow-up."""
    session = models.OneToOneField(ChatSession, on_delete=models.CASCADE, related_name="search_context")
    filters_json = models.JSONField()
    last_result_ids = models.JSONField(default=list)
    updated_at = models.DateTimeField(auto_now=True)
