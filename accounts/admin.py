# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Role, Permission, RolePermission, UserRole, UserActionHistory, MembershipPlan, MembershipOrder

# -------- User --------
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Các field hiển thị theo form của huynh
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
    list_display = ('id', 'username', 'email', 'so_dien_thoai', 'is_staff', 'get_roles')
    search_fields = ('username', 'email')
    ordering = ('username',)

    def get_roles(self, obj):
        return ", ".join([role.role_name for role in obj.roles.all()])
    get_roles.short_description = 'Roles'

# -------- UserActionHistory --------
@admin.register(UserActionHistory)
class UserActionHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'bai_dang', 'action_type', 'timestamp')
    list_filter = ('action_type', 'timestamp')
    list_select_related = ('user', 'bai_dang')
    autocomplete_fields = ('user', 'bai_dang')

# -------- UserRole --------
@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'role', 'assigned_at', 'expires_at', 'is_active', 'granted_by')
    list_filter = ('is_active', 'assigned_at', 'expires_at')
    list_select_related = ('user', 'role', 'granted_by')
    autocomplete_fields = ('user', 'role', 'granted_by')
    search_fields = ('user__username', 'user__email', 'role__role_name')

# -------- Permission --------
@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'ten_quyen', 'mo_ta', 'code')
    search_fields = ('ten_quyen', 'code')

# -------- RolePermission --------
@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'role', 'permission')
    search_fields = ('role__role_name', 'permission__ten_quyen')
    list_select_related = ('role', 'permission')

# -------- Role --------
@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'role_name', 'mo_ta')
    search_fields = ('role_name',)

@admin.register(MembershipPlan)
class MembershipPlanAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'name', 'price_vnd', 'duration_days', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('code', 'name')
@admin.register(MembershipOrder)
class MembershipOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'plan', 'amount_vnd', 'status', 'bank_ref', 'transfer_note', 'created_at', 'paid_at')
    list_filter = ('status', 'created_at', 'paid_at')
    search_fields = ('user__username', 'user__email', 'bank_ref', 'transfer_note')
    list_select_related = ('user', 'plan')