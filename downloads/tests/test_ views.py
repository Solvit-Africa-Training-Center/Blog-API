from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from downloads.models import DownloadLog
from blog.models import BlogPost, Category
from django.http import HttpResponse

User = get_user_model()


class DownloadEndpointsTest(APITestCase):
    """Tests for downloads app endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )

        # Monkeypatch create_download_response to a simple HttpResponse for tests
        import downloads.views as dl_views
        dl_views.create_download_response = lambda content, filename, content_type: HttpResponse(content, content_type=content_type)

        self.category = Category.objects.create(
            name='Test Category',
            description='desc'
        )

        self.public_post = BlogPost.objects.create(
            title='Public Post',
            content='content',
            author=self.user,
            category=self.category,
            is_public=True,
            status='published'
        )
        self.private_post = BlogPost.objects.create(
            title='Private Post',
            content='content',
            author=self.user,
            category=self.category,
            is_public=False,
            status='published'
        )

    def get_tokens_for_user(self, user):
        refresh = RefreshToken.for_user(user)
        return {'access': str(refresh.access_token), 'refresh': str(refresh)}

    def test_historical_posts_requires_auth(self):
        url = reverse('downloads:historical_posts')
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_my_posts_requires_auth(self):
        url = reverse('downloads:my_posts')
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_historical_posts_success_json(self):
        tokens = self.get_tokens_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        url = reverse('downloads:historical_posts')
        data = {
            'format': 'json',
            'include_private': True,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # A log should be created and marked successful
        log = DownloadLog.objects.first()
        self.assertIsNotNone(log)
        self.assertTrue(log.is_successful)
        self.assertEqual(log.download_type, DownloadLog.HISTORICAL_POSTS)

    def test_historical_posts_invalid_date_range(self):
        tokens = self.get_tokens_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        url = reverse('downloads:historical_posts')
        data = {
            'format': 'json',
            'date_from': '2024-12-31',
            'date_to': '2024-01-01'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_my_posts_success_csv(self):
        tokens = self.get_tokens_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        url = reverse('downloads:my_posts')
        data = {'format': 'csv'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        log = DownloadLog.objects.first()
        self.assertIsNotNone(log)
        self.assertEqual(log.download_type, DownloadLog.USER_POSTS)

    def test_my_posts_invalid_format(self):
        tokens = self.get_tokens_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        url = reverse('downloads:my_posts')
        data = {'format': 'pdf'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_usage_stats_requires_auth(self):
        url = reverse('downloads:usage_stats')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_usage_stats_returns_logs_and_stats(self):
        # Create some logs for both users
        DownloadLog.objects.create(
            user=self.user,
            download_type=DownloadLog.HISTORICAL_POSTS,
            file_format='json',
            ip_address='127.0.0.1',
            is_successful=True,
            total_records=10,
            file_size_bytes=100,
            processing_time_seconds=0.5,
        )
        DownloadLog.objects.create(
            user=self.user,
            download_type=DownloadLog.USER_POSTS,
            file_format='csv',
            ip_address='127.0.0.1',
            is_successful=False,
        )
        DownloadLog.objects.create(
            user=self.other_user,
            download_type=DownloadLog.USER_POSTS,
            file_format='xml',
            ip_address='127.0.0.1',
            is_successful=True,
        )

        tokens = self.get_tokens_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        url = reverse('downloads:usage_stats')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Non-paginated path returns dict with results and usage_stats
        self.assertIn('results', response.data)
        self.assertIn('usage_stats', response.data)
        stats = response.data['usage_stats']
        self.assertIn('total_downloads', stats)
        self.assertIn('successful_downloads', stats)
        self.assertIn('failed_downloads', stats)
        self.assertIn('total_data_downloaded_mb', stats)
        self.assertIn('can_download_now', stats)

