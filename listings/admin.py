from django.contrib import admin
from .models import Post, PostType, Category, ApprovalStatus, PostStatus, PostHistory, PostImage

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'post_type',
        'category',
        'price',
        'area',
        'created_at',
        'owner_id',      # id chủ bài
    )
    search_fields = (
        'title',
        'description',
        'owner_id',      # cho phép search theo id chủ bài
    )
    list_filter = (
        'post_type',
        'category',
        'created_at',
    )
    # chỉ dùng các field quan hệ trong list_select_related
    list_select_related = (
        'post_type',
        'category',
        'approval_status',
        'post_status',
    )
    # autocomplete chỉ áp dụng cho FK / M2M
    autocomplete_fields = (
        'post_type',
        'category',
        'approval_status',
        'post_status',
    )
    ordering = ('-created_at',)


@admin.register(PostType)
class PostTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(ApprovalStatus)
class ApprovalStatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    ordering = ('name',)


@admin.register(PostStatus)
class PostStatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    ordering = ('name',)


@admin.register(PostHistory)
class PostHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'post',
        'actor_id',      # id người thao tác (đã đổi từ owner_id)
        'change_type',
        'timestamp',
    )
    search_fields = (
        'post__title',
        'change_type',
        'actor_id',      # search theo id người thao tác
    )
    list_filter = (
        'change_type',
        'timestamp',
    )
    # chỉ FK post là quan hệ, actor_id là CharField nên không đưa vào đây
    list_select_related = ('post',)
    autocomplete_fields = ('post',)
    ordering = ('-timestamp',)

@admin.register(PostImage)
class PostImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'created_at')
    search_fields = ('post__title',)
    list_filter = ('created_at',)
    list_select_related = ('post',)
    autocomplete_fields = ('post',)
    ordering = ('-created_at',)