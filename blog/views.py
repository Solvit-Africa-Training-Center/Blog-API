# ===== blog/views.py =====
from rest_framework import viewsets, generics, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle, ScopedRateThrottle
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404
from .models import BlogPost, Category, Tag
from .serializers import (
    BlogPostListSerializer,
    BlogPostDetailSerializer,
    BlogPostCreateUpdateSerializer,
    CategorySerializer,
    TagSerializer
)
from .permissions import IsAuthorOrReadOnly, CanViewPost
from .filters import BlogPostFilter

class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing categories
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name']
    search_fields = ['name', 'description']
    ordering = ['name']
    
    def get_permissions(self):
        """
        Only staff users can create/update/delete categories
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

class TagViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing tags
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name']
    search_fields = ['name']
    ordering = ['name']
    
    def get_permissions(self):
        """
        Any authenticated user can create tags, only staff can delete
        """
        if self.action == 'destroy':
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

class PostCreateThrottle(ScopedRateThrottle):
    """
    Custom throttle for post creation
    """
    scope = 'posts'

class BlogPostViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing blog posts with advanced features
    """
    permission_classes = [permissions.IsAuthenticated, IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = BlogPostFilter
    search_fields = ['title', 'content', 'excerpt']
    ordering_fields = ['created_at', 'publication_date', 'view_count', 'like_count']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Return posts based on user permissions
        """
        user = self.request.user
        
        if self.action == 'list':
            # For list view, show public published posts + user's own posts
            return BlogPost.objects.filter(
                Q(is_public=True, status='published') |
                Q(author=user)
            ).select_related('author', 'category').prefetch_related('tags')
        else:
            # For detail views, use object-level permissions
            return BlogPost.objects.all().select_related(
                'author', 'category'
            ).prefetch_related('tags')
    
    def get_serializer_class(self):
        """
        Return different serializers based on action
        """
        if self.action == 'list':
            return BlogPostListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return BlogPostCreateUpdateSerializer
        else:
            return BlogPostDetailSerializer
    
    def get_permissions(self):
        """
        Set permissions based on action
        """
        if self.action == 'retrieve':
            return [permissions.IsAuthenticated(), CanViewPost()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsAuthorOrReadOnly()]
        return [permissions.IsAuthenticated()]
    
    def get_throttles(self):
        """
        Apply throttling for post creation
        """
        if self.action == 'create':
            return [PostCreateThrottle()]
        return [UserRateThrottle()]
    
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a post and increment view count
        """
        instance = self.get_object()
        
        # Increment view count (only once per user per session)
        session_key = f'viewed_post_{instance.id}'
        if not request.session.get(session_key, False):
            instance.increment_view_count()
            request.session[session_key] = True
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_posts(self, request):
        """
        Get current user's posts
        """
        posts = BlogPost.objects.filter(
            author=request.user
        ).select_related('category').prefetch_related('tags')
        
        # Apply filtering
        filterset = BlogPostFilter(request.GET, queryset=posts)
        posts = filterset.qs
        
        page = self.paginate_queryset(posts)
        if page is not None:
            serializer = BlogPostListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = BlogPostListSerializer(posts, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def public_posts(self, request):
        """
        Get all public published posts
        """
        posts = BlogPost.objects.filter(
            is_public=True,
            status='published'
        ).select_related('author', 'category').prefetch_related('tags')
        
        # Apply filtering
        filterset = BlogPostFilter(request.GET, queryset=posts)
        posts = filterset.qs
        
        page = self.paginate_queryset(posts)
        if page is not None:
            serializer = BlogPostListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = BlogPostListSerializer(posts, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """
        Like/unlike a post
        """
        post = self.get_object()
        
        # Simple like system (in production, you'd want a separate Like model)
        session_key = f'liked_post_{post.id}'
        if request.session.get(session_key, False):
            # Unlike
            post.like_count = max(0, post.like_count - 1)
            request.session[session_key] = False
            action = 'unliked'
        else:
            # Like
            post.like_count += 1
            request.session[session_key] = True
            action = 'liked'
        
        post.save(update_fields=['like_count'])
        
        return Response({
            'action': action,
            'like_count': post.like_count
        })
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """
        Get popular posts based on views and likes
        """
        posts = BlogPost.objects.filter(
            is_public=True,
            status='published'
        ).annotate(
            popularity=Count('view_count') + Count('like_count')
        ).order_by('-popularity')[:10]
        
        serializer = BlogPostListSerializer(posts, many=True, context={'request': request})
        return Response(serializer.data)