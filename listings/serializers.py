# listings/serializers.py
from rest_framework import serializers
from listings.models import PostImage 
from listings.models import Post
from .models import Category
from .models import PostType
class PostCreateUpdateSerializer(serializers.Serializer):
    # required khi create; optional khi update (partial=True)
    title = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False, allow_blank=True)

    # json fields
    address = serializers.JSONField(required=False)   # {province,district,ward,street}
    location = serializers.JSONField(required=False)  # {lat,lng}
    details = serializers.JSONField(required=False)   # {bedrooms,bathrooms,...}
    other_info = serializers.JSONField(required=False, allow_null=True)

    # numeric
    area = serializers.FloatField(required=False)
    price = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)

    # FK
    post_type_id = serializers.IntegerField(required=False)
    category_id  = serializers.IntegerField(required=False)

    def validate(self, attrs):
        # nếu là create: enforce required
        if self.instance is None and not self.partial:
            required = ["title","description","address","location","details",
                        "area","price","post_type_id","category_id"]
            missing = [k for k in required if k not in attrs]
            if missing:
                raise serializers.ValidationError(
                    {"missing": f"Thiếu trường: {', '.join(missing)}"}
                )
        return attrs
    
class PostImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = PostImage
        # Trả về id, url và created_at là đủ xài
        fields = ["id", "image_url", "created_at"]

    def get_image_url(self, obj):
        if not obj.image:
            return None

        url = obj.image.url  # local: /media/... ; Cloudinary: https://...

        request = self.context.get("request")
        # Nếu là local dev, url có thể là "/media/..." → build absolute URL đầy đủ
        if request is not None and url and not url.startswith("http"):
            return request.build_absolute_uri(url)

        return url
    
class PostSerializer(serializers.ModelSerializer):
    images = PostImageSerializer(many=True, read_only=True)   # <–– thêm dòng này

    class Meta:
        model = Post
        fields = [
            "id",
            "title",
            "description",
            "address",
            "location",
            "details",
            "other_info",
            "area",
            "price",
            "post_type",
            "category",
            "owner_id",
            "approval_status",
            "post_status",
            "created_at",
            "updated_at",
            "is_deleted",
            "images",       # <–– và thêm images vào list fields
        ]
class PostListSerializer(serializers.ModelSerializer):
    """
    Serializer dùng cho:
    - API listing
    - Chatbot trả về danh sách tin gợi ý
    """

    # Hiển thị tên loại tin & loại BĐS dạng text cho FE xài luôn
    post_type = serializers.CharField(source="post_type.name", read_only=True)
    category = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Post
        # Huynh chọn những field cần thiết, không nên nhét hết cho nặng
        fields = [
            "id",
            "title",
            "description",
            "address",
            "location",
            "details",
            "area",
            "price",
            "post_type",
            "category",
            "owner_id",
            "bumped_at",
            "created_at",
            "owner_is_agent",
        ]
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]
class PostTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostType
        fields = ["id", "name"]