from django.contrib import admin
from .models import User, Post, PostType, Category, Role,  ApprovalStatus, PostStatus, UserRole, Permission, RolePermission, Notification, UserActionHistory, UserFavorite, Messenger, LienHe, PostHistory, PostRating
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin


class UserAdmin(BaseUserAdmin):
    # Loại bỏ field permissions và groups
    fieldsets = (
        (None, {'fields': ('username', 'email', 'so_dien_thoai')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'so_dien_thoai', 'password1', 'password2'),
        }),
    )

    list_display = ('id','username', 'email', 'so_dien_thoai', 'is_staff')
    search_fields = ('username', 'email')
    ordering = ('username',)
    def get_roles(self, obj):
        return ", ".join([role.role_name for role in obj.roles.all()])
    get_roles.short_description = 'Roles'
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'post_type', 'category', 'price', 'area', 'created_at', 'user')
    search_fields = ('title', 'description')
    list_filter = ('post_type', 'category', 'created_at')
    list_select_related = ('user', 'post_type', 'category')  # tối ưu query
class PostTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'role_name')
class ApprovalStatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
class PostStatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'role', 'assigned_at', 'expires_at', 'is_active', 'granted_by')
    list_filter = ('is_active', 'assigned_at', 'expires_at')
    list_select_related = ('user', 'role', 'granted_by')  # tối ưu query
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'ten_quyen', 'mo_ta')
    search_fields = ('ten_quyen',)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'role', 'permission')
    search_fields = ('role__role_name', 'permission__ten_quyen')
    list_select_related = ('role', 'permission')  # tối ưu query
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'content', 'is_read', 'created_at')  # sửa 'message' -> 'content'
    search_fields = ( 'title', 'content')
    list_filter = ('is_read', 'created_at')
    list_select_related = ('user',)

# -------- UserActionHistory --------
class UserActionHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'bai_dang', 'action_type', 'timestamp')  # 'description' -> 'bai_dang'
    list_filter = ('action_type', 'timestamp')
    list_select_related = ('user', 'bai_dang')

# -------- UserFavorite --------
class UserFavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'bai_dang', 'ngay_tao')  # 'post', 'favorited_at' -> 'bai_dang', 'ngay_tao'
    list_filter = ('ngay_tao',)
    list_select_related = ('user', 'bai_dang')

# -------- Messenger --------
class MessengerAdmin(admin.ModelAdmin):
    list_display = ('id', 'nguoi_gui', 'nguoi_nhan', 'noi_dung', 'thoi_gian', 'is_read')  # 'sender'->'nguoi_gui', 'receiver'->'nguoi_nhan', 'message'->'noi_dung', 'sent_at'->'thoi_gian'
    list_filter = ('is_read', 'thoi_gian')
    list_select_related = ('nguoi_gui', 'nguoi_nhan')

# -------- LienHe --------
class LienHeAdmin(admin.ModelAdmin):
    list_display = ('id', 'bai_dang', 'nguoi_lien_he', 'noi_dung', 'ngay_lien_he')  # sửa theo model
    list_filter = ('ngay_lien_he',)
    list_select_related = ('bai_dang', 'nguoi_lien_he')

# -------- PostHistory --------
class PostHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'user', 'change_type', 'timestamp')
    search_fields = ('post__title', 'change_type')
    list_filter = ('change_type', 'timestamp')
    list_select_related = ('post', 'user')

# -------- PostRating --------
class PostRatingAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'user', 'rating', 'comment', 'created_at')  # 'rated_at' -> 'created_at'
    search_fields = ('post__title', 'comment')
    list_filter = ('rating', 'created_at')
    list_select_related = ('post', 'user')
admin.site.register(Notification, NotificationAdmin)
admin.site.register(UserActionHistory, UserActionHistoryAdmin)  
admin.site.register(UserFavorite, UserFavoriteAdmin) 
admin.site.register(Messenger, MessengerAdmin)
admin.site.register(LienHe, LienHeAdmin)
admin.site.register(PostHistory, PostHistoryAdmin)
admin.site.register(PostRating, PostRatingAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(Post, PostAdmin)    
admin.site.register(PostType, PostTypeAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Role, RoleAdmin)
admin.site.register(ApprovalStatus, ApprovalStatusAdmin)
admin.site.register(PostStatus, PostStatusAdmin)
admin.site.register(UserRole, UserRoleAdmin)
admin.site.register(Permission, PermissionAdmin)
admin.site.register(RolePermission, RolePermissionAdmin)

# Register your models here.
