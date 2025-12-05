from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from ..models import *
from ..serializers import * 
from django.contrib.auth.hashers import check_password
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")

# --- Signup ---
@api_view(['POST'])
def signup(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()  # set_password đã được handle trong serializer
        return Response({"message": "User created successfully"}, status=status.HTTP_201_CREATED)
    return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# --- Login ---
@api_view(['POST'])
def login(request):
    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response({"error": "Email và mật khẩu bắt buộc"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({"error": "Email hoặc mật khẩu không đúng"}, status=status.HTTP_400_BAD_REQUEST)

    if not user.check_password(password):
        return Response({"error": "Email hoặc mật khẩu không đúng"}, status=status.HTTP_400_BAD_REQUEST)

    # # Trả thông tin user nếu đăng nhập thành công
    # user_data = UserSerializer(user).data
    # return Response({
    #     "message": "Đăng nhập thành công",
    #     "user": user_data
    # }, status=status.HTTP_200_OK)
     # Tạo JWT token
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)

    user_data = UserSerializer(user).data
    return Response({
        "message": "Đăng nhập thành công",
        "access": access_token,
        "refresh": refresh_token,
        "user": user_data
    }, status=status.HTTP_200_OK)
# --- Logout ---
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    refresh_token = request.data.get("refresh")
    if not refresh_token:
        return Response({"error": "Thiếu refresh token"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"message": "Đăng xuất thành công"}, status=status.HTTP_200_OK)
    except Exception:
        return Response({"error": "Token không hợp lệ"}, status=status.HTTP_400_BAD_REQUEST)
# ---------------------------
# 1️⃣ LẤY THÔNG TIN NGƯỜI DÙNG
# ---------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user(request, user_id):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return Response({"error": "Không tìm thấy người dùng"}, status=status.HTTP_404_NOT_FOUND)

    # Chỉ chính chủ hoặc admin mới được xem
    if request.user != user and not request.user.is_staff:
        return Response({"error": "Không có quyền truy cập"}, status=status.HTTP_403_FORBIDDEN)

    serializer = UserSerializer(user)
    return Response(serializer.data, status=status.HTTP_200_OK)


# ---------------------------
# 2️⃣ CẬP NHẬT THÔNG TIN NGƯỜI DÙNG
# ---------------------------
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_user(request, user_id):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return Response({"error": "Không tìm thấy người dùng"}, status=status.HTTP_404_NOT_FOUND)

    # Chỉ chính chủ hoặc admin mới được chỉnh sửa
    if request.user != user and not request.user.is_staff:
        return Response({"error": "Không có quyền chỉnh sửa"}, status=status.HTTP_403_FORBIDDEN)

    serializer = UserSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "Cập nhật thông tin thành công",
            "user": serializer.data
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ---------------------------
# 3️⃣ XÓA (VÔ HIỆU HÓA) NGƯỜI DÙNG
# ---------------------------
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_user(request, user_id):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return Response({"error": "Không tìm thấy người dùng"}, status=status.HTTP_404_NOT_FOUND)

    if not request.user.is_staff and request.user != user:
        return Response({"error": "Không có quyền xóa người dùng này"}, status=status.HTTP_403_FORBIDDEN)

    # Nếu muốn xóa mềm
    user.is_active = False
    user.save()
    return Response({"message": "Tài khoản đã được vô hiệu hóa thành công"}, status=status.HTTP_200_OK)