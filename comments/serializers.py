
# ===== comments/serializers.py =====
from rest_framework import serializers
from .models import Comment
from blog.models import BlogPost

class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for comments with nested replies support
    """
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    author_username = serializers.CharField(source='author.username', read_only=True)
    author_avatar = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()
    post_title = serializers.CharField(source='post.title', read_only=True)
    is_author = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'content', 'author_name', 'author_username', 'author_avatar',
            'post', 'post_title', 'parent', 'replies', 'is_approved', 'is_edited',
            'is_author', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'author_name', 'author_username', 'author_avatar', 'post_title',
            'is_approved', 'is_edited', 'is_author', 'created_at', 'updated_at'
        ]
    
    def get_author_avatar(self, obj):
        if obj.author.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.author.avatar.url)
        return None
    
    def get_replies(self, obj):
        """Get nested replies (limited to 2 levels)"""
        if obj.parent is None:  # Only get replies for top-level comments
            replies = obj.replies.filter(is_approved=True).order_by('created_at')
            return CommentSerializer(replies, many=True, context=self.context).data
        return []
    
    def get_is_author(self, obj):
        """Check if current user is the comment author"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.author == request.user
        return False
    
    def validate_content(self, value):
        """Validate comment content"""
        content = value.strip()
        if len(content) < 3:
            raise serializers.ValidationError("Comment must be at least 3 characters long.")
        if len(content) > 1000:
            raise serializers.ValidationError("Comment cannot exceed 1000 characters.")
        return content
    
    def validate_post(self, value):
        """Validate that the post exists and allows comments"""
        if not value.is_published():
            raise serializers.ValidationError("Cannot comment on unpublished posts.")
        return value
    
    def validate_parent(self, value):
        """Validate parent comment"""
        if value:
            # Check if parent comment belongs to the same post
            post = self.initial_data.get('post')
            if post and value.post_id != int(post):
                raise serializers.ValidationError("Parent comment must belong to the same post.")
            
            # Prevent nested replies beyond 1 level
            if value.parent is not None:
                raise serializers.ValidationError("Cannot reply to a reply. Please reply to the original comment.")
        
        return value
    
    def create(self, validated_data):
        """Create comment with current user as author"""
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)

class CommentCreateSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for creating comments
    """
    class Meta:
        model = Comment
        fields = ['content', 'post', 'parent']
    
    def validate_content(self, value):
        content = value.strip()
        if len(content) < 3:
            raise serializers.ValidationError("Comment must be at least 3 characters long.")
        if len(content) > 1000:
            raise serializers.ValidationError("Comment cannot exceed 1000 characters.")
        return content
    
    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)

# ===== downloads/serializers.py =====
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
        read_only_fields = '__all__'
    
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