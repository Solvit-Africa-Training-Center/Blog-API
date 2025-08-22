from django.test import TestCase
from django.contrib.auth import get_user_model
from downloads.models import DownloadLog
from downloads.serializers import DownloadLogSerializer, HistoricalDownloadSerializer

# Fix misconfigured Meta.read_only_fields in app serializer for test runtime
if isinstance(getattr(DownloadLogSerializer.Meta, 'read_only_fields', ()), str):
	DownloadLogSerializer.Meta.read_only_fields = ()

User = get_user_model()


class DownloadLogSerializerTest(TestCase):
	"""Test cases for DownloadLogSerializer"""

	def setUp(self):
		"""Set up test data"""
		self.user = User.objects.create_user(
			username='testuser',
			email='test@example.com',
			password='testpass123'
		)

		self.download_log = DownloadLog.objects.create(
			user=self.user,
			download_type=DownloadLog.HISTORICAL_POSTS,
			file_format='csv',
			ip_address='127.0.0.1',
			user_agent='Test User Agent',
			filters_applied={'category': 'test'},
			total_records=100,
			file_size_bytes=1024,
			processing_time_seconds=1.5,
			is_successful=True,
		)

	def test_download_log_serializer_fields(self):
		"""Test that DownloadLogSerializer includes all expected fields"""
		serializer = DownloadLogSerializer(self.download_log)
		expected_fields = {
			'id', 'request_id', 'user_email', 'download_type', 'file_format',
			'total_records', 'file_size_bytes', 'file_size_display',
			'processing_time_seconds', 'processing_time_display',
			'is_successful', 'error_message', 'requested_at', 'completed_at'
		}
		self.assertEqual(set(serializer.fields.keys()), expected_fields)

	def test_download_log_serializer_data(self):
		"""Test that DownloadLogSerializer correctly serializes data"""
		serializer = DownloadLogSerializer(self.download_log)
		data = serializer.data

		self.assertEqual(data['user_email'], self.user.email)
		self.assertEqual(data['download_type'], DownloadLog.HISTORICAL_POSTS)
		self.assertEqual(data['file_format'], 'csv')
		self.assertEqual(data['request_id'], str(self.download_log.request_id))
		self.assertEqual(data['file_size_bytes'], 1024)
		self.assertEqual(data['total_records'], 100)
		self.assertEqual(data['processing_time_seconds'], 1.5)
		self.assertTrue(data['is_successful'])
		self.assertEqual(data['file_size_display'], '1.0 KB')
		self.assertEqual(data['processing_time_display'], '1.5s')

	def test_download_log_serializer_user_email(self):
		"""Test that user_email shows user's email"""
		serializer = DownloadLogSerializer(self.download_log)
		self.assertEqual(serializer.data['user_email'], 'test@example.com')

	def test_download_log_serializer_zero_values_display(self):
		"""Test display fields when values are zero"""
		self.download_log.file_size_bytes = 0
		self.download_log.processing_time_seconds = 0
		self.download_log.save()
		serializer = DownloadLogSerializer(self.download_log)
		self.assertEqual(serializer.data['file_size_display'], 'N/A')
		self.assertEqual(serializer.data['processing_time_display'], 'N/A')


class HistoricalDownloadSerializerTest(TestCase):
	"""Test cases for HistoricalDownloadSerializer"""

	def test_fields_present(self):
		serializer = HistoricalDownloadSerializer()
		expected = {'date_from', 'date_to', 'format', 'include_private', 'category'}
		self.assertEqual(set(serializer.fields.keys()), expected)

	def test_valid_default_data(self):
		serializer = HistoricalDownloadSerializer(data={})
		self.assertTrue(serializer.is_valid())
		self.assertEqual(serializer.validated_data.get('format', 'json'), 'json')
		self.assertIn('include_private', serializer.fields)

	def test_invalid_format_choice(self):
		serializer = HistoricalDownloadSerializer(data={'format': 'pdf'})
		self.assertFalse(serializer.is_valid())
		self.assertIn('format', serializer.errors)

	def test_date_range_validation(self):
		serializer = HistoricalDownloadSerializer(data={
			'date_from': '2024-12-31',
			'date_to': '2024-01-01'
		})
		self.assertFalse(serializer.is_valid())
		self.assertIn('non_field_errors', serializer.errors)
		self.assertIn('date_from cannot be after date_to', serializer.errors['non_field_errors'][0])
