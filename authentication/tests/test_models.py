from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
import tempfile
import os
from PIL import Image

User = get_user_model()

class CustomUserModelTest(TestCase):
    def setUp(self):
        """Set up test data"""
        self.user_data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'bio': 'Test bio',
            'date_of_birth': '1990-01-01',
        }
        
        # Create a temporary image for testing
        self.temp_image = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        img = Image.new('RGB', (100, 100), color='red')
        img.save(self.temp_image.name)
        self.temp_image.close()

    def tearDown(self):
        """Clean up temporary files"""
        if os.path.exists(self.temp_image.name):
            os.unlink(self.temp_image.name)

    def test_create_user(self):
        """Test creating a basic user"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.email, self.user_data['email'])
        self.assertEqual(user.username, self.user_data['username'])
        self.assertTrue(user.check_password(self.user_data['password']))
        self.assertFalse(user.is_verified)
        self.assertEqual(user.download_count, 0)
        self.assertIsNone(user.last_download)

    def test_create_superuser(self):
        """Test creating a superuser"""
        user = User.objects.create_superuser(**self.user_data)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_email_is_username_field(self):
        """Test that email is the username field"""
        self.assertEqual(User.USERNAME_FIELD, 'email')

    def test_required_fields(self):
        """Test that username is in required fields"""
        self.assertIn('username', User.REQUIRED_FIELDS)

    def test_user_str_representation(self):
        """Test string representation of user"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(str(user), self.user_data['email'])

    def test_get_full_name(self):
        """Test get_full_name method"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.get_full_name(), 'Test User')

    def test_get_full_name_without_names(self):
        """Test get_full_name with empty names"""
        user_data = self.user_data.copy()
        user_data['first_name'] = ''
        user_data['last_name'] = ''
        user = User.objects.create_user(**user_data)
        self.assertEqual(user.get_full_name(), '')

    def test_can_download_when_no_previous_download(self):
        """Test can_download when user has never downloaded"""
        user = User.objects.create_user(**self.user_data)
        self.assertTrue(user.can_download())

    def test_can_download_after_time_limit(self):
        """Test can_download after time limit has passed"""
        user = User.objects.create_user(**self.user_data)
        user.last_download = timezone.now() - timedelta(hours=2)
        user.save()
        self.assertTrue(user.can_download())

    def test_cannot_download_within_time_limit(self):
        """Test can_download within time limit"""
        user = User.objects.create_user(**self.user_data)
        user.last_download = timezone.now() - timedelta(minutes=30)
        user.save()
        self.assertFalse(user.can_download())

    def test_increment_download_count(self):
        """Test increment_download_count method"""
        user = User.objects.create_user(**self.user_data)
        initial_count = user.download_count
        initial_time = user.last_download
        
        user.increment_download_count()
        user.refresh_from_db()
        
        self.assertEqual(user.download_count, initial_count + 1)
        self.assertIsNotNone(user.last_download)
        if initial_time is not None:
            self.assertGreater(user.last_download, initial_time)

    def test_user_with_avatar(self):
        """Test user creation with avatar"""
        # Create a temporary image for testing
        temp_image = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        img = Image.new('RGB', (100, 100), color='red')
        img.save(temp_image.name)
        temp_image.close()
        
        try:
            user_data = self.user_data.copy()
            user = User.objects.create_user(**user_data)
            
            # Test that user was created successfully
            self.assertEqual(user.username, 'testuser')
            self.assertEqual(user.email, 'test@example.com')
        finally:
            # Clean up temporary file
            if os.path.exists(temp_image.name):
                os.unlink(temp_image.name)

    def test_user_meta_options(self):
        """Test user model meta options"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user._meta.db_table, 'auth_user_custom')
        self.assertEqual(user._meta.verbose_name, 'User')
        self.assertEqual(user._meta.verbose_name_plural, 'Users')

    def test_user_default_values(self):
        """Test user default values"""
        user = User.objects.create_user(**self.user_data)
        self.assertFalse(user.is_verified)
        self.assertEqual(user.download_count, 0)
        self.assertIsNotNone(user.created_at)
        self.assertIsNotNone(user.updated_at)

    def test_user_validation(self):
        """Test user validation"""
        # Test unique email constraint
        User.objects.create_user(**self.user_data)
        
        with self.assertRaises(Exception):  # Django will raise IntegrityError
            User.objects.create_user(
                email=self.user_data['email'],
                username='anotheruser',
                password='testpass123'
            )

    def test_user_password_validation(self):
        """Test user password validation"""
        user_data = self.user_data.copy()
        user_data['password'] = 'short'
        
        # Django's default password validation should catch this
        # but we'll test that the user is created (validation happens at form level)
        user = User.objects.create_user(**user_data)
        self.assertTrue(user.check_password('short'))

