# ===== comments/views.py =====
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Comment
from .serializers import CommentSerializer, CommentCreateSerializer
from .permissions import IsCommentAuthorOrReadOnly
from blog.models import BlogPost

class CommentCreateThrottle(ScopedRateThrottle):
    """
    Custom throttle for comment creation
    """
    scope = 'comments'

class CommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing comments
    """
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, IsCommentAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['post', 'is_approved']
    ordering = ['created_at']
    
    def get_queryset(self):
        """
        Return approved comments, plus user's own comments
        """
        user = self.request.user
        return Comment.objects.filter(
            Q(is_approved=True) | Q(author=user)
        ).select_related('author', 'post', 'parent')
    
    def get_serializer_class(self):
        """
        Use different serializers for create vs other actions
        """
        if self.action == 'create':
            return CommentCreateSerializer
        return CommentSerializer
    
    def get_throttles(self):
        """
        Apply throttling for comment creation
        """
        if self.action == 'create':
            return [CommentCreateThrottle()]
        return super().get_throttles()
    
    @action(detail=False, methods=['get'], url_path='post/(?P<post_id>[^/.]+)')
    def by_post(self, request, post_id=None):
        """
        Get comments for a specific post
        """
        post = get_object_or_404(BlogPost, id=post_id)
        
        # Check if user can view the post
        if not post.can_be_viewed_by(request.user):
            return Response(
                {'error': 'You do not have permission to view comments for this post'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get top-level comments only (replies are nested)
        comments = Comment.objects.filter(
            post=post,
            parent=None,
            is_approved=True
        ).select_related('author').order_by('created_at')
        
        page = self.paginate_queryset(comments)
        if page is not None:
            serializer = CommentSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = CommentSerializer(comments, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_comments(self, request):
        """
        Get current user's comments
        """
        comments = Comment.objects.filter(
            author=request.user
        ).select_related('post').order_by('-created_at')
        
        page = self.paginate_queryset(comments)
        if page is not None:
            serializer = CommentSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = CommentSerializer(comments, many=True, context={'request': request})
        return Response(serializer.data)