# ===== blog/serializers.py =====
from rest_framework import serializers
from django.utils import timezone
from .models import Category, Tag, BlogPost

class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for Category model
    """
    posts_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'slug', 'posts_count', 'created_at']
        read_only_fields = ['slug', 'created_at']
    
    def get_posts_count(self, obj):
        return obj.posts.filter(status='published', is_public=True).count()

class TagSerializer(serializers.ModelSerializer):
    """
    Serializer for Tag model
    """
    posts_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'posts_count', 'created_at']
        read_only_fields = ['slug', 'created_at']
    
    def get_posts_count(self, obj):
        return obj.posts.filter(status='published', is_public=True).count()

class BlogPostListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for blog post lists
    """
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    author_username = serializers.CharField(source='author.username', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    comments_count = serializers.SerializerMethodField()
    reading_time = serializers.SerializerMethodField()
    
    class Meta:
        model = BlogPost
        fields = [
            'id', 'title', 'slug', 'excerpt', 'author_name', 'author_username',
            'category_name', 'tags', 'is_public', 'status', 'featured_image',
            'publication_date', 'created_at', 'view_count', 'like_count',
            'comments_count', 'reading_time'
        ]
    
    def get_comments_count(self, obj):
        return obj.comments.filter(is_approved=True).count()
    
    def get_reading_time(self, obj):
        """Estimate reading time based on word count (250 words per minute)"""
        word_count = len(obj.content.split())
        return max(1, round(word_count / 250))

class BlogPostDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for individual blog posts
    """
    author = serializers.SerializerMethodField()
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    comments_count = serializers.SerializerMethodField()
    reading_time = serializers.SerializerMethodField()
    
    class Meta:
        model = BlogPost
        fields = [
            'id', 'title', 'slug', 'content', 'excerpt', 'author',
            'category', 'tags', 'is_public', 'status', 'meta_description',
            'featured_image', 'publication_date', 'created_at', 'updated_at',
            'view_count', 'like_count', 'comments_count', 'reading_time'
        ]
        read_only_fields = [
            'slug', 'view_count', 'like_count', 'created_at', 'updated_at'
        ]
    
    def get_author(self, obj):
        return {
            'id': obj.author.id,
            'username': obj.author.username,
            'full_name': obj.author.get_full_name(),
            'avatar': obj.author.avatar.url if obj.author.avatar else None,
            'bio': obj.author.bio
        }
    
    def get_comments_count(self, obj):
        return obj.comments.filter(is_approved=True).count()
    
    def get_reading_time(self, obj):
        word_count = len(obj.content.split())
        return max(1, round(word_count / 250))

class BlogPostCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating blog posts
    """
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=False
    )
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = BlogPost
        fields = [
            'title', 'content', 'excerpt', 'category', 'tags',
            'is_public', 'status', 'meta_description', 'featured_image'
        ]
    
    def validate_title(self, value):
        """Validate title length and uniqueness for the author"""
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Title must be at least 5 characters long.")
        
        # Check for duplicate titles by the same author (excluding current instance)
        user = self.context['request'].user
        queryset = BlogPost.objects.filter(author=user, title=value)
        
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise serializers.ValidationError("You already have a post with this title.")
        
        return value.strip()
    
    def validate_content(self, value):
        """Validate content length"""
        if len(value.strip()) < 100:
            raise serializers.ValidationError("Content must be at least 100 characters long.")
        return value.strip()
    
    def validate_tags(self, value):
        """Validate tags count"""
        if len(value) > 10:
            raise serializers.ValidationError("A post cannot have more than 10 tags.")
        return value
    
    def create(self, validated_data):
        """Create blog post with current user as author"""
        tags = validated_data.pop('tags', [])
        validated_data['author'] = self.context['request'].user
        
        post = BlogPost.objects.create(**validated_data)
        post.tags.set(tags)
        return post
    
    def update(self, instance, validated_data):
        """Update blog post"""
        tags = validated_data.pop('tags', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        
        if tags is not None:
            instance.tags.set(tags)
        
        return instance
