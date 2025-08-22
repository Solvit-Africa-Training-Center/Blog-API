from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from ..models import DownloadLog
import uuid

User = get_user_model()

class DownloadLogModelTest(TestCase):
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        
        self.download_log_data = {
            'user': self.user,
            'download_type': DownloadLog.HISTORICAL_POSTS,
            'file_format': 'json',
            'ip_address': '127.0.0.1',
            'user_agent': 'Mozilla/5.0 (Test Browser)',
            'filters_applied': {'category': 'technology', 'date_from': '2023-01-01'},
            'total_records': 0,
            'file_size_bytes': 0,
            'processing_time_seconds': 0.0,
            'is_successful': False,
        }

    def test_create_download_log(self):
        """Test creating a basic download log"""
        download_log = DownloadLog.objects.create(**self.download_log_data)
        
        self.assertEqual(download_log.user, self.user)
        self.assertEqual(download_log.download_type, DownloadLog.HISTORICAL_POSTS)
        self.assertEqual(download_log.file_format, 'json')
        self.assertEqual(download_log.ip_address, '127.0.0.1')
        self.assertEqual(download_log.user_agent, 'Mozilla/5.0 (Test Browser)')
        self.assertEqual(download_log.filters_applied, {'category': 'technology', 'date_from': '2023-01-01'})
        self.assertEqual(download_log.total_records, 0)
        self.assertEqual(download_log.file_size_bytes, 0)
        self.assertEqual(download_log.processing_time_seconds, 0.0)
        self.assertFalse(download_log.is_successful)
        self.assertEqual(download_log.error_message, '')
        self.assertIsNotNone(download_log.request_id)
        self.assertIsNotNone(download_log.requested_at)
        self.assertIsNone(download_log.completed_at)

    def test_download_log_str_representation(self):
        """Test string representation of download log"""
        download_log = DownloadLog.objects.create(**self.download_log_data)
        expected_str = f"{self.user.username} - {DownloadLog.HISTORICAL_POSTS} at {download_log.requested_at}"
        self.assertEqual(str(download_log), expected_str)

    def test_download_log_choices(self):
        """Test download log type choices"""
        self.assertEqual(DownloadLog.HISTORICAL_POSTS, 'historical_posts')
        self.assertEqual(DownloadLog.USER_POSTS, 'user_posts')
        self.assertEqual(DownloadLog.CATEGORY_POSTS, 'category_posts')
        
        # Test valid download type
        download_log = DownloadLog.objects.create(**self.download_log_data)
        download_log.download_type = DownloadLog.USER_POSTS
        download_log.save()
        self.assertEqual(download_log.download_type, DownloadLog.USER_POSTS)

    def test_download_log_file_format_choices(self):
        """Test file format choices"""
        # Test JSON format
        download_log = DownloadLog.objects.create(**self.download_log_data)
        self.assertEqual(download_log.file_format, 'json')
        
        # Test CSV format
        download_log.file_format = 'csv'
        download_log.save()
        self.assertEqual(download_log.file_format, 'csv')
        
        # Test XML format
        download_log.file_format = 'xml'
        download_log.save()
        self.assertEqual(download_log.file_format, 'xml')

    def test_download_log_request_id_unique(self):
        """Test request ID uniqueness"""
        download_log1 = DownloadLog.objects.create(**self.download_log_data)
        download_log2 = DownloadLog.objects.create(**self.download_log_data)
        
        # Each should have a unique request ID
        self.assertNotEqual(download_log1.request_id, download_log2.request_id)
        
        # Request IDs should be UUIDs
        self.assertIsInstance(download_log1.request_id, uuid.UUID)
        self.assertIsInstance(download_log2.request_id, uuid.UUID)

    def test_download_log_meta_options(self):
        """Test download log model meta options"""
        download_log = DownloadLog.objects.create(**self.download_log_data)
        self.assertEqual(download_log._meta.ordering, ['-requested_at'])

    def test_download_log_indexes(self):
        """Test download log model indexes"""
        download_log = DownloadLog.objects.create(**self.download_log_data)
        indexes = download_log._meta.indexes
        index_fields = [index.fields for index in indexes]
        
        self.assertIn(['user', 'requested_at'], index_fields)
        self.assertIn(['download_type', 'requested_at'], index_fields)

    def test_download_log_relationships(self):
        """Test download log relationships"""
        download_log = DownloadLog.objects.create(**self.download_log_data)
        
        # Test user relationship
        self.assertEqual(download_log.user, self.user)
        self.assertIn(download_log, self.user.download_logs.all())

    def test_download_log_mark_completed(self):
        """Test mark_completed method"""
        download_log = DownloadLog.objects.create(**self.download_log_data)
        
        # Mark as completed
        download_log.mark_completed(
            total_records=100,
            file_size=1024,
            processing_time=1.5
        )
        
        # Refresh from database
        download_log.refresh_from_db()
        
        # Check completion status
        self.assertTrue(download_log.is_successful)
        self.assertEqual(download_log.total_records, 100)
        self.assertEqual(download_log.file_size_bytes, 1024)
        self.assertEqual(download_log.processing_time_seconds, 1.5)
        self.assertIsNotNone(download_log.completed_at)

    def test_download_log_mark_failed(self):
        """Test mark_failed method"""
        download_log = DownloadLog.objects.create(**self.download_log_data)
        
        # Mark as failed
        error_message = "Download failed due to network error"
        download_log.mark_failed(error_message)
        
        # Refresh from database
        download_log.refresh_from_db()
        
        # Check failure status
        self.assertFalse(download_log.is_successful)
        self.assertEqual(download_log.error_message, error_message)
        self.assertIsNotNone(download_log.completed_at)

    def test_download_log_mark_completed_default_values(self):
        """Test mark_completed method with default values"""
        download_log = DownloadLog.objects.create(**self.download_log_data)
        
        # Mark as completed with default values
        download_log.mark_completed()
        
        # Refresh from database
        download_log.refresh_from_db()
        
        # Check default values
        self.assertTrue(download_log.is_successful)
        self.assertEqual(download_log.total_records, 0)
        self.assertEqual(download_log.file_size_bytes, 0)
        self.assertEqual(download_log.processing_time_seconds, 0.0)

    def test_download_log_validation(self):
        """Test download log validation"""
        # Test required fields
        invalid_data = {}
        
        with self.assertRaises(Exception):  # Django will raise IntegrityError
            DownloadLog.objects.create(**invalid_data)

    def test_download_log_ip_address_validation(self):
        """Test IP address validation"""
        # Test valid IPv4
        valid_ipv4_data = self.download_log_data.copy()
        valid_ipv4_data['ip_address'] = '192.168.1.1'
        download_log = DownloadLog.objects.create(**valid_ipv4_data)
        self.assertEqual(download_log.ip_address, '192.168.1.1')
        
        # Test valid IPv6
        valid_ipv6_data = self.download_log_data.copy()
        valid_ipv6_data['ip_address'] = '::1'
        download_log = DownloadLog.objects.create(**valid_ipv6_data)
        self.assertEqual(download_log.ip_address, '::1')

    def test_download_log_filters_applied_json(self):
        """Test filters_applied JSON field"""
        # Test with complex filters
        complex_filters = {
            'category': 'technology',
            'date_range': {
                'from': '2023-01-01',
                'to': '2023-12-31'
            },
            'tags': ['python', 'django'],
            'author': 'testuser',
            'status': 'published'
        }
        
        filters_data = self.download_log_data.copy()
        filters_data['filters_applied'] = complex_filters
        
        download_log = DownloadLog.objects.create(**filters_data)
        
        # Verify filters were stored correctly
        self.assertEqual(download_log.filters_applied, complex_filters)
        self.assertEqual(download_log.filters_applied['category'], 'technology')
        self.assertEqual(download_log.filters_applied['tags'], ['python', 'django'])

    def test_download_log_filters_applied_empty(self):
        """Test filters_applied with empty dict"""
        empty_filters_data = self.download_log_data.copy()
        empty_filters_data['filters_applied'] = {}
        
        download_log = DownloadLog.objects.create(**empty_filters_data)
        
        # Verify empty filters were stored correctly
        self.assertEqual(download_log.filters_applied, {})

    def test_download_log_ordering(self):
        """Test download log ordering by requested time"""
        # Create download logs with different timestamps
        download_log1 = DownloadLog.objects.create(**self.download_log_data)
        
        # Simulate time delay
        import time
        time.sleep(0.001)
        
        download_log2_data = self.download_log_data.copy()
        download_log2_data['download_type'] = DownloadLog.USER_POSTS
        download_log2 = DownloadLog.objects.create(**download_log2_data)
        
        # Test ordering (newest first)
        download_logs = DownloadLog.objects.all()
        self.assertEqual(download_logs[0], download_log2)  # Newest first
        self.assertEqual(download_logs[1], download_log1)  # Oldest last

    def test_download_log_user_agent_blank(self):
        """Test user agent can be blank"""
        blank_user_agent_data = self.download_log_data.copy()
        blank_user_agent_data['user_agent'] = ''
        
        download_log = DownloadLog.objects.create(**blank_user_agent_data)
        self.assertEqual(download_log.user_agent, '')

    def test_download_log_error_message_blank(self):
        """Test error message can be blank"""
        blank_error_data = self.download_log_data.copy()
        blank_error_data['error_message'] = ''
        
        download_log = DownloadLog.objects.create(**blank_error_data)
        self.assertEqual(download_log.error_message, '')

    def test_download_log_processing_time_float(self):
        """Test processing time as float"""
        # Test with decimal processing time
        processing_time_data = self.download_log_data.copy()
        processing_time_data['processing_time_seconds'] = 2.75
        
        download_log = DownloadLog.objects.create(**processing_time_data)
        self.assertEqual(download_log.processing_time_seconds, 2.75)

    def test_download_log_file_size_positive(self):
        """Test file size as positive integer"""
        # Test with positive file size
        file_size_data = self.download_log_data.copy()
        file_size_data['file_size_bytes'] = 2048
        
        download_log = DownloadLog.objects.create(**file_size_data)
        self.assertEqual(download_log.file_size_bytes, 2048)

    def test_download_log_total_records_positive(self):
        """Test total records as positive integer"""
        # Test with positive total records
        total_records_data = self.download_log_data.copy()
        total_records_data['total_records'] = 500
        
        download_log = DownloadLog.objects.create(**total_records_data)
        self.assertEqual(download_log.total_records, 500)

    def test_download_log_timestamps(self):
        """Test download log timestamps"""
        before_creation = timezone.now()
        
        download_log = DownloadLog.objects.create(**self.download_log_data)
        
        after_creation = timezone.now()
        
        # requested_at should be between before and after
        self.assertGreaterEqual(download_log.requested_at, before_creation)
        self.assertLessEqual(download_log.requested_at, after_creation)
        
        # completed_at should be None initially
        self.assertIsNone(download_log.completed_at)

    def test_download_log_completion_timestamp(self):
        """Test download log completion timestamp"""
        download_log = DownloadLog.objects.create(**self.download_log_data)
        
        before_completion = timezone.now()
        
        # Mark as completed
        download_log.mark_completed()
        
        after_completion = timezone.now()
        
        # completed_at should be between before and after
        self.assertGreaterEqual(download_log.completed_at, before_completion)
        self.assertLessEqual(download_log.completed_at, after_completion)

    def test_download_log_cascade_delete_user(self):
        """Test download log deletion when user is deleted"""
        download_log = DownloadLog.objects.create(**self.download_log_data)
        
        # Delete the user
        self.user.delete()
        
        # Download log should also be deleted
        self.assertFalse(DownloadLog.objects.filter(pk=download_log.pk).exists())

    def test_download_log_request_id_uniqueness(self):
        """Test request ID uniqueness across multiple logs"""
        # Create multiple download logs
        download_logs = []
        for i in range(10):
            log_data = self.download_log_data.copy()
            log_data['download_type'] = DownloadLog.USER_POSTS if i % 2 == 0 else DownloadLog.CATEGORY_POSTS
            download_log = DownloadLog.objects.create(**log_data)
            download_logs.append(download_log)
        
        # All request IDs should be unique
        request_ids = [log.request_id for log in download_logs]
        unique_request_ids = set(request_ids)
        self.assertEqual(len(request_ids), len(unique_request_ids))

    def test_download_log_status_transitions(self):
        """Test download log status transitions"""
        download_log = DownloadLog.objects.create(**self.download_log_data)
        
        # Initially not successful
        self.assertFalse(download_log.is_successful)
        self.assertEqual(download_log.error_message, '')
        
        # Mark as completed
        download_log.mark_completed()
        self.assertTrue(download_log.is_successful)
        self.assertEqual(download_log.error_message, '')
        
        # Mark as failed (this would typically require recreating or updating)
        # For this test, we'll just verify the method works
        download_log.mark_failed("New error occurred")
        self.assertFalse(download_log.is_successful)
        self.assertEqual(download_log.error_message, "New error occurred")

