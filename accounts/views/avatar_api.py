from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.storage import default_storage
from ..serializers import MeSerializer

class MeAvatarView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]


    def post(self, request, *args, **kwargs):
        f = request.FILES.get("avatar")
        if not f:
            return Response({"detail": "avatar file is required"}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user

        # ✅ chỉ lưu "name" cũ (string), không giữ FieldFile object
        old_name = getattr(user.anh_dai_dien, "name", None)

        # lưu ảnh mới
        user.anh_dai_dien = f
        user.save(update_fields=["anh_dai_dien"])

        # ✅ refresh để chắc chắn instance có name/url mới
        user.refresh_from_db(fields=["anh_dai_dien"])
        new_name = getattr(user.anh_dai_dien, "name", None)

        # ✅ xoá file cũ trên storage (Cloudinary) nếu khác file mới
        if old_name and old_name != new_name:
            try:
                default_storage.delete(old_name)  # hoặc user.anh_dai_dien.storage.delete(old_name)
            except Exception:
                pass

        return Response(MeSerializer(user, context={"request": request}).data, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        user = request.user
        user.anh_dai_dien = None
        user.save(update_fields=["anh_dai_dien"])
        return Response({"ok": 1}, status=status.HTTP_200_OK)
