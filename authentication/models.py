# ===== authentication/models.py =====
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class CustomUser(AbstractUser):
    """
    Extended User model with additional fields for the blog API
    """
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
  
    
    # Track API usage
    last_download = models.DateTimeField(null=True, blank=True)
    download_count = models.PositiveIntegerField(default=0)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'auth_user_custom'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def can_download(self):
        """Check if user can download based on rate limiting"""
        if not self.last_download:
            return True
        
        time_diff = timezone.now() - self.last_download
        # Allow download if last download was more than 1 hour ago
        return time_diff.total_seconds() > 3600
    
    def increment_download_count(self):
        """Track download usage"""
        self.download_count += 1
        self.last_download = timezone.now()
        self.save(update_fields=['download_count', 'last_download'])