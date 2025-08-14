# ===== downloads/throttles.py =====
from rest_framework.throttling import UserRateThrottle
from django.core.cache import cache
import time

class DownloadRateThrottle(UserRateThrottle):
    """
    Custom throttle for download endpoints with enhanced security
    """
    scope = 'downloads'
    
    def allow_request(self, request, view):
        """
        Override to add additional security checks
        """
        # Basic rate limiting
        if not super().allow_request(request, view):
            return False
        
        # Additional check for authenticated users
        if request.user.is_authenticated:
            # Check user-specific download cooldown
            if not request.user.can_download():
                return False
        
        return True
    
    def get_cache_key(self, request, view):
        """
        Create cache key for throttling
        """
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }
