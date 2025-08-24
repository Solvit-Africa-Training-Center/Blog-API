from rest_framework import serializers
from .models import DownloadLog

class HistoricalDownloadSerializer(serializers.Serializer):
    """
    Serializer for historical posts download requests
    """
    date_from = serializers.DateField(required=False, help_text="Download posts from this date")
    date_to = serializers.DateField(required=False, help_text="Download posts until this date")
    format = serializers.ChoiceField(
        choices=['json', 'csv', 'xml'],
        default='json',
        help_text="File format for download"
    )
    include_private = serializers.BooleanField(
        default=False,
        help_text="Include your private posts"
    )
    category = serializers.CharField(
        required=False,
        help_text="Filter by category name"
    )
    
    def validate(self, attrs):
        """Validate date range"""
        date_from = attrs.get('date_from')
        date_to = attrs.get('date_to')
        
        if date_from and date_to:
            if date_from > date_to:
                raise serializers.ValidationError("date_from cannot be after date_to")
        
        return attrs

class DownloadLogSerializer(serializers.ModelSerializer):
    """
    Serializer for download logs
    """
    user_email = serializers.CharField(source='user.email', read_only=True)
    processing_time_display = serializers.SerializerMethodField()
    file_size_display = serializers.SerializerMethodField()
    
    class Meta:
        model = DownloadLog
        fields = [
            'id', 'request_id', 'user_email', 'download_type', 'file_format',
            'total_records', 'file_size_bytes', 'file_size_display',
            'processing_time_seconds', 'processing_time_display',
            'is_successful', 'error_message', 'requested_at', 'completed_at'
        ]
        read_only_fields = fields
    
    def get_processing_time_display(self, obj):
        """Convert processing time to human readable format"""
        if obj.processing_time_seconds == 0:
            return 'N/A'
        
        seconds = obj.processing_time_seconds
        if seconds < 1:
            return f"{seconds * 1000:.0f}ms"
        elif seconds < 60:
            return f"{seconds:.1f}s"
        else:
            minutes = seconds // 60
            remaining_seconds = seconds % 60
            return f"{minutes:.0f}m {remaining_seconds:.0f}s"
    
    def get_file_size_display(self, obj):
        """Convert file size to human readable format"""
        if obj.file_size_bytes == 0:
            return 'N/A'
        
        size = obj.file_size_bytes
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"