from rest_framework import serializers
from .models import User, Post, PostType, Category, ApprovalStatus, PostStatus
from django.contrib.auth.hashers import make_password, check_password

# Serializer cho User
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # các trường cần hiển thị
        fields = ['id', 'email', 'so_dien_thoai', 'roles', 'address', 'da_xac_minh', 'bio']

# Serializer cho đăng ký người dùng
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['email',  'password', 'so_dien_thoai'] 

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)  

        user.save()
        return user

# Serializer cho đăng nhập
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Email hoặc mật khẩu không đúng.")

        # Dùng check_password() của Django (đã hash)
        if not user.check_password(password):
            raise serializers.ValidationError("Email hoặc mật khẩu không đúng.")

        data['user'] = user
        return data

## Serializer cho PostType
class PostTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostType
        fields = ['id', 'name']

# Serializer cho Category
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class ApprovalStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalStatus
        fields = ['id', 'name', 'description']  
class PostStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostStatus
        fields = ['id', 'name', 'description']

# Serializer cho Post
class PostSerializer(serializers.ModelSerializer):
    post_type = PostTypeSerializer(read_only=True)
    category = CategorySerializer(read_only=True)

    post_type_id = serializers.PrimaryKeyRelatedField(
        queryset=PostType.objects.all(), source="post_type", write_only=True
    )
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source="category", write_only=True
    )

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'description', 
            'address', 'location', 'details', 'other_info',
            'area', 'price',
            'post_type', 'category',
            'post_type_id', 'category_id',
            'created_at', 'user'
        ] 