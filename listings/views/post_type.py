from rest_framework import generics, permissions
from listings.models import PostType
from listings.serializers import PostTypeSerializer

class PostTypeListAPIView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = PostTypeSerializer

    def get_queryset(self):
        return PostType.objects.all().order_by("name")
