# ===== comments/admin.py =====
from django.contrib import admin
from .models import Comment

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['short_content', 'author', 'post_title', 'is_approved', 'is_reply', 'created_at']
    list_filter = ['is_approved', 'is_edited', 'created_at', 'post__category']
    search_fields = ['content', 'author__username', 'post__title']
    readonly_fields = ['is_edited', 'created_at', 'updated_at']
    raw_id_fields = ['post', 'parent']
    
    fieldsets = [
        ('Content', {
            'fields': ('content', 'author', 'post')
        }),
        ('Threading', {
            'fields': ('parent',)
        }),
        ('Status', {
            'fields': ('is_approved', 'is_edited', 'created_at', 'updated_at')
        }),
    ]
    
    def short_content(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    short_content.short_description = 'Content'
    
    def post_title(self, obj):
        return obj.post.title
    post_title.short_description = 'Post'
    
    def is_reply(self, obj):
        return obj.parent is not None
    is_reply.boolean = True
    is_reply.short_description = 'Reply'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('author', 'post', 'parent')
