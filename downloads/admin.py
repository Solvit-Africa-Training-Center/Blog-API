# ===== downloads/admin.py =====
from django.contrib import admin
from django.utils.html import format_html
from .models import DownloadLog

@admin.register(DownloadLog)
class DownloadLogAdmin(admin.ModelAdmin):
    list_display = [
        'request_id_short', 'user', 'download_type', 'file_format', 
        'total_records', 'file_size_display', 'status_display', 'requested_at'
    ]
    list_filter = [
        'download_type', 'file_format', 'is_successful', 
        'requested_at', 'completed_at'
    ]
    search_fields = ['user__username', 'user__email', 'request_id', 'ip_address']
    readonly_fields = [
        'request_id', 'requested_at', 'completed_at', 
        'processing_time_seconds', 'ip_address', 'user_agent'
    ]
    
    fieldsets = [
        ('Request Info', {
            'fields': ('request_id', 'user', 'download_type', 'file_format')
        }),
        ('Client Details', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ['collapse']
        }),
        ('Parameters', {
            'fields': ('filters_applied',)
        }),
        ('Results', {
            'fields': ('total_records', 'file_size_bytes', 'processing_time_seconds')
        }),
        ('Status', {
            'fields': ('is_successful', 'error_message', 'requested_at', 'completed_at')
        }),
    ]
    
    def request_id_short(self, obj):
        return str(obj.request_id)[:8] + "..."
    request_id_short.short_description = 'Request ID'
    
    def file_size_display(self, obj):
        if obj.file_size_bytes == 0:
            return '-'
        
        # Convert bytes to human readable format
        for unit in ['B', 'KB', 'MB', 'GB']:
            if obj.file_size_bytes < 1024.0:
                return f"{obj.file_size_bytes:.1f} {unit}"
            obj.file_size_bytes /= 1024.0
        return f"{obj.file_size_bytes:.1f} TB"
    file_size_display.short_description = 'File Size'
    
    def status_display(self, obj):
        if obj.is_successful:
            return format_html('<span style="color: green;">✓ Success</span>')
        elif obj.completed_at:
            return format_html('<span style="color: red;">✗ Failed</span>')
        else:
            return format_html('<span style="color: orange;">⏳ Processing</span>')
    status_display.short_description = 'Status'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
