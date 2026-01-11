from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.parsers import MultiPartParser, FormParser

from ..serializers import MeSerializer

class MeAvatarView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        # field name: "avatar"
        f = request.FILES.get("avatar")
        if not f:
            return Response({"detail": "avatar file is required"}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        user.anh_dai_dien = f
        user.save(update_fields=["anh_dai_dien"])

        return Response(MeSerializer(user, context={"request": request}).data, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        user = request.user
        user.anh_dai_dien = None
        user.save(update_fields=["anh_dai_dien"])
        return Response({"ok": 1}, status=status.HTTP_200_OK)
