
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import ScopedRateThrottle
from django.db.models import Q
from django.utils import timezone
from django.http import HttpResponse
from blog.models import BlogPost, Category
from .models import DownloadLog
from .serializers import HistoricalDownloadSerializer, DownloadLogSerializer
from .utils import DataExporter, get_client_ip, create_download_response
import time
import logging

logger = logging.getLogger('blog_api')

class DownloadThrottle(ScopedRateThrottle):
    """
    Strict throttling for download endpoints
    """
    scope = 'downloads'

class HistoricalPostsDownloadView(APIView):
    """
    OANDA-style secure historical posts download endpoint
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [DownloadThrottle]
    
    def post(self, request):
        """
        Download historical posts with security checks
        """
        start_time = time.time()
        
        # Validate request data
        serializer = HistoricalDownloadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data
        user = request.user
        
        # Security check: Rate limiting at user level
        if not user.can_download():
            return Response({
                'error': 'Download rate limit exceeded. Please wait before requesting another download.',
                'retry_after': 3600  # seconds
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Create download log entry
        download_log = DownloadLog.objects.create(
            user=user,
            download_type=DownloadLog.HISTORICAL_POSTS,
            file_format=validated_data.get('format', 'json'),
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            filters_applied=dict(request.data)
        )
        
        try:
            # Build queryset based on filters
            queryset = self._build_queryset(user, validated_data)
            
            # Security check: Limit maximum records
            max_records = 10000  # Adjust as needed
            if queryset.count() > max_records:
                download_log.mark_failed(f"Too many records requested. Maximum allowed: {max_records}")
                return Response({
                    'error': f'Too many records requested. Maximum allowed: {max_records}',
                    'requested_count': queryset.count()
                }, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
            
            # Export data
            file_format = validated_data.get('format', 'json')
            content, content_type, file_extension = self._export_data(queryset, file_format)
            
            # Calculate metrics
            processing_time = time.time() - start_time
            file_size = len(content.encode('utf-8'))
            
            # Log successful download
            download_log.mark_completed(
                total_records=queryset.count(),
                file_size=file_size,
                processing_time=processing_time
            )
            
            # Update user download tracking
            user.increment_download_count()
            
            # Create filename
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            filename = f'historical_posts_{timestamp}.{file_extension}'
            
            logger.info(f"User {user.username} downloaded {queryset.count()} posts in {processing_time:.2f}s")
            
            return create_download_response(content, filename, content_type)
            
        except Exception as e:
            logger.error(f"Download failed for user {user.username}: {str(e)}")
            download_log.mark_failed(str(e))
            return Response({
                'error': 'Download failed. Please try again later.',
                'request_id': str(download_log.request_id)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _build_queryset(self, user, filters):
        """
        Build queryset based on user permissions and filters
        """
        # Base queryset: public posts + user's own posts
        queryset = BlogPost.objects.filter(
            Q(is_public=True, status='published') |
            Q(author=user)
        ).select_related('author', 'category').prefetch_related('tags')
        
        # Apply date filters with timezone awareness
        if filters.get('date_from'):
            date_from = filters['date_from']
            # Ensure timezone awareness
            if timezone.is_naive(date_from):
                date_from = timezone.make_aware(date_from)
            queryset = queryset.filter(publication_date__gte=date_from)
        
        if filters.get('date_to'):
            date_to = filters['date_to']
            # Ensure timezone awareness
            if timezone.is_naive(date_to):
                date_to = timezone.make_aware(date_to)
            queryset = queryset.filter(publication_date__lte=date_to)
        
        # Category filter
        if filters.get('category'):
            try:
                category = Category.objects.get(name__icontains=filters['category'])
                queryset = queryset.filter(category=category)
            except Category.DoesNotExist:
                logger.warning(f"Category not found: {filters['category']}")
                pass
        
        # Include private posts only if requested and they belong to user
        if not filters.get('include_private', False):
            queryset = queryset.filter(Q(is_public=True) | Q(author=user, is_public=False))
        
        return queryset.order_by('-created_at')
    
    def _export_data(self, queryset, file_format):
        """
        Export data in specified format
        """
        if file_format == 'csv':
            content = DataExporter.export_posts_to_csv(queryset)
            content_type = 'text/csv'
            file_extension = 'csv'
        elif file_format == 'xml':
            content = DataExporter.export_posts_to_xml(queryset)
            content_type = 'application/xml'
            file_extension = 'xml'
        else:  # Default to JSON
            content = DataExporter.export_posts_to_json(queryset)
            content_type = 'application/json'
            file_extension = 'json'
        
        return content, content_type, file_extension

class UserPostsDownloadView(APIView):
    """
    Download current user's posts
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [DownloadThrottle]
    
    def post(self, request):
        """
        Download user's own posts
        """
        start_time = time.time()
        user = request.user
        
        # Get format from request
        file_format = request.data.get('format', 'json')
        if file_format not in ['json', 'csv', 'xml']:
            return Response({
                'error': 'Invalid format. Supported formats: json, csv, xml'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create download log
        download_log = DownloadLog.objects.create(
            user=user,
            download_type=DownloadLog.USER_POSTS,
            file_format=file_format,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            filters_applied={'format': file_format}
        )
        
        try:
            # Get user's posts
            queryset = BlogPost.objects.filter(
                author=user
            ).select_related('category').prefetch_related('tags').order_by('-created_at')
            
            # Export data
            content, content_type, file_extension = self._export_data(queryset, file_format)
            
            # Calculate metrics
            processing_time = time.time() - start_time
            file_size = len(content.encode('utf-8'))
            
            # Log successful download
            download_log.mark_completed(
                total_records=queryset.count(),
                file_size=file_size,
                processing_time=processing_time
            )
            
            # Create filename
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            filename = f'my_posts_{timestamp}.{file_extension}'
            
            logger.info(f"User {user.username} downloaded their {queryset.count()} posts")
            
            return create_download_response(content, filename, content_type)
            
        except Exception as e:
            logger.error(f"User posts download failed for {user.username}: {str(e)}")
            download_log.mark_failed(str(e))
            return Response({
                'error': 'Download failed. Please try again later.',
                'request_id': str(download_log.request_id)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _export_data(self, queryset, file_format):
        """
        Export data in specified format
        """
        if file_format == 'csv':
            content = DataExporter.export_posts_to_csv(queryset)
            content_type = 'text/csv'
            file_extension = 'csv'
        elif file_format == 'xml':
            content = DataExporter.export_posts_to_xml(queryset)
            content_type = 'application/xml'
            file_extension = 'xml'
        else:  # Default to JSON
            content = DataExporter.export_posts_to_json(queryset)
            content_type = 'application/json'
            file_extension = 'json'
        
        return content, content_type, file_extension

class DownloadUsageView(generics.ListAPIView):
    """
    View user's download history and usage statistics
    """
    serializer_class = DownloadLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return DownloadLog.objects.filter(
            user=self.request.user
        ).order_by('-requested_at')
    
    def list(self, request, *args, **kwargs):
        """
        Return download logs with usage statistics
        """
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            
            # Add usage statistics
            stats = self._get_usage_stats(request.user)
            
            response_data = self.get_paginated_response(serializer.data).data
            response_data['usage_stats'] = stats
            
            return Response(response_data)
        
        serializer = self.get_serializer(queryset, many=True)
        stats = self._get_usage_stats(request.user)
        
        return Response({
            'results': serializer.data,
            'usage_stats': stats
        })
    
    def _get_usage_stats(self, user):
        """
        Calculate usage statistics for the user
        """
        logs = DownloadLog.objects.filter(user=user)
        
        total_downloads = logs.count()
        successful_downloads = logs.filter(is_successful=True).count()
        failed_downloads = logs.filter(is_successful=False).count()
        
        # Calculate total data downloaded (handle None values)
        total_bytes = sum(
            log.file_size_bytes or 0 for log in logs.filter(is_successful=True)
        )
        total_data_mb = total_bytes / (1024 * 1024)
        
        # Recent activity (last 30 days)
        recent_date = timezone.now() - timezone.timedelta(days=30)
        recent_downloads = logs.filter(requested_at__gte=recent_date).count()
        
        return {
            'total_downloads': total_downloads,
            'successful_downloads': successful_downloads,
            'failed_downloads': failed_downloads,
            'success_rate': round((successful_downloads / total_downloads * 100) if total_downloads > 0 else 0, 2),
            'total_data_downloaded_mb': round(total_data_mb, 2),
            'recent_downloads_30_days': recent_downloads,
            'last_download': user.last_download.isoformat() if user.last_download else None,
            'can_download_now': user.can_download()
        }