# ===== comments/models.py =====
from django.db import models
from django.conf import settings
from blog.models import BlogPost

class Comment(models.Model):
    """
    Comments on blog posts with threading support
    """
    content = models.TextField(max_length=1000)
    
    # Relationships
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='comments'
    )
    post = models.ForeignKey(
        BlogPost, 
        on_delete=models.CASCADE, 
        related_name='comments'
    )
    parent = models.ForeignKey(
        'self', 
        null=True, 
        blank=True, 
        on_delete=models.CASCADE, 
        related_name='replies'
    )
    
    # Status and moderation
    is_approved = models.BooleanField(default=True)
    is_edited = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['post', 'created_at']),
            models.Index(fields=['author']),
        ]
    
    def __str__(self):
        return f"Comment by {self.author.username} on {self.post.title}"
    
    def save(self, *args, **kwargs):
        # Mark as edited if content is being updated
        if self.pk:
            original = Comment.objects.get(pk=self.pk)
            if original.content != self.content:
                self.is_edited = True
        
        super().save(*args, **kwargs)
    
    def is_reply(self):
        return self.parent is not None
    
    def get_replies(self):
        return Comment.objects.filter(parent=self)