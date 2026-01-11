# chatbot/api.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .engine import handle_message
from listings.serializers import PostListSerializer  # huynh đã có


class ChatbotAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        session_id = request.data.get("session_id") or request.session.session_key
        if not session_id:
            request.session.create()
            session_id = request.session.session_key

        message = (request.data.get("message") or "").strip()
        if not message:
            return Response({"error": "message is required"}, status=400)

        result = handle_message(
            session_id=session_id,
            user_message=message,
            user=request.user if request.user.is_authenticated else None,
        )

        serializer = PostListSerializer(result["results"], many=True)

        return Response({
            "session_id": result["session_id"],
            "answer": result["answer"],
            "intent": result["intent"],
            "filters": result["filters"],
            "results": serializer.data,
        })
