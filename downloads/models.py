# ===== downloads/models.py =====
from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

class DownloadLog(models.Model):
    """
    Track download requests for security and analytics
    """
    HISTORICAL_POSTS = 'historical_posts'
    USER_POSTS = 'user_posts'
    CATEGORY_POSTS = 'category_posts'
    
    DOWNLOAD_TYPES = [
        (HISTORICAL_POSTS, 'Historical Posts'),
        (USER_POSTS, 'User Posts'),
        (CATEGORY_POSTS, 'Category Posts'),
    ]
    
    # Tracking fields
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='download_logs'
    )
    download_type = models.CharField(max_length=50, choices=DOWNLOAD_TYPES)
    file_format = models.CharField(max_length=10, default='json')  # json, csv, xml
    
    # Request details
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    request_id = models.UUIDField(default=uuid.uuid4, unique=True)
    
    # Filter parameters used
    filters_applied = models.JSONField(default=dict, blank=True)
    
    # Results
    total_records = models.PositiveIntegerField(default=0)
    file_size_bytes = models.PositiveIntegerField(default=0)
    processing_time_seconds = models.FloatField(default=0.0)
    
    # Status
    is_successful = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    
    # Timestamps
    requested_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['user', 'requested_at']),
            models.Index(fields=['download_type', 'requested_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.download_type} at {self.requested_at}"
    
    def mark_completed(self, total_records=0, file_size=0, processing_time=0.0):
        """Mark download as completed successfully"""
        self.is_successful = True
        self.total_records = total_records
        self.file_size_bytes = file_size
        self.processing_time_seconds = processing_time
        self.completed_at = timezone.now()
        self.save()
    
    def mark_failed(self, error_message):
        """Mark download as failed"""
        self.is_successful = False
        self.error_message = error_message
        self.completed_at = timezone.now()
        self.save()