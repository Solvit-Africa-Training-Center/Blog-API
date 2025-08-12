# ===== blog/admin.py =====
from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Tag, BlogPost

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'post_count', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    def post_count(self, obj):
        return obj.posts.count()
    post_count.short_description = 'Posts'

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'post_count', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']
    readonly_fields = ['created_at']
    
    def post_count(self, obj):
        return obj.posts.count()
    post_count.short_description = 'Posts'

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'status', 'is_public', 'view_count', 'created_at']
    list_filter = ['status', 'is_public', 'category', 'created_at', 'publication_date']
    search_fields = ['title', 'content', 'author__username', 'author__email']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['tags']
    readonly_fields = ['view_count', 'like_count', 'created_at', 'updated_at']
    
    fieldsets = [
        ('Content', {
            'fields': ('title', 'slug', 'content', 'excerpt', 'featured_image')
        }),
        ('Classification', {
            'fields': ('author', 'category', 'tags')
        }),
        ('Visibility & Status', {
            'fields': ('is_public', 'status', 'publication_date')
        }),
        ('SEO', {
            'fields': ('meta_description',),
            'classes': ['collapse']
        }),
        ('Statistics', {
            'fields': ('view_count', 'like_count', 'created_at', 'updated_at'),
            'classes': ['collapse']
        }),
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('author', 'category')