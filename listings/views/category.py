from rest_framework import generics, permissions
from listings.models import Category
from listings.serializers import CategorySerializer

class CategoryListAPIView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = CategorySerializer

    def get_queryset(self):
        return Category.objects.all().order_by("name")
