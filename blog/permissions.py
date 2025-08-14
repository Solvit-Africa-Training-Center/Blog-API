# ===== blog/permissions.py =====
from rest_framework import permissions
from rest_framework.permissions import BasePermission

class IsAuthorOrReadOnly(BasePermission):
    """
    Custom permission to only allow authors to edit their own posts
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for the author
        return obj.author == request.user

class CanViewPost(BasePermission):
    """
    Permission to check if user can view a specific post
    """
    def has_object_permission(self, request, view, obj):
        # Use the model's can_be_viewed_by method
        return obj.can_be_viewed_by(request.user)

class IsCommentAuthorOrReadOnly(BasePermission):
    """
    Custom permission for comments
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for the comment author
        return obj.author == request.user