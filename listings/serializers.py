# listings/serializers.py
from rest_framework import serializers

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
