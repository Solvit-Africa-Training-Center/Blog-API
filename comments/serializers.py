# comments/serializers.py
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