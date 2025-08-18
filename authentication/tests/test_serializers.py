from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import serializers
from authentication.serializers import UserRegistrationSerializer, UserProfileSerializer
from datetime import date

User = get_user_model()


class UserRegistrationSerializerTest(TestCase):
    """Test cases for UserRegistrationSerializer"""

    def setUp(self):
        """Set up test data"""
        self.valid_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'bio': 'Test bio',
            'date_of_birth': '1990-01-01'
        }

    def test_valid_registration_data(self):
        """Test serializer with valid data"""
        serializer = UserRegistrationSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())

    def test_password_mismatch(self):
        """Test password mismatch validation"""
        data = self.valid_data.copy()
        data['password_confirm'] = 'differentpassword'
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

    def test_missing_required_fields(self):
        """Test missing required fields"""
        # Test missing username
        data = self.valid_data.copy()
        del data['username']
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)
        
        # Test missing email
        data = self.valid_data.copy()
        del data['email']
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
        
        # Test missing password
        data = self.valid_data.copy()
        del data['password']
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)
        
        # Test missing password_confirm
        data = self.valid_data.copy()
        del data['password_confirm']
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password_confirm', serializer.errors)

    def test_invalid_username_length(self):
        """Test username length validation"""
        data = self.valid_data.copy()
        data['username'] = 'ab'  # Too short
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)

    def test_duplicate_email(self):
        """Test duplicate email validation"""
        # Create a user first
        User.objects.create_user(
            username='existinguser',
            email='test@example.com',
            password='testpass123'
        )
        
        serializer = UserRegistrationSerializer(data=self.valid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_duplicate_username(self):
        """Test duplicate username validation"""
        # Create a user first
        User.objects.create_user(
            username='testuser',
            email='existing@example.com',
            password='testpass123'
        )
        
        serializer = UserRegistrationSerializer(data=self.valid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)

    def test_optional_fields(self):
        """Test optional fields are not required"""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123'
        }
        serializer = UserRegistrationSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_serializer_save(self):
        """Test serializer save method creates user"""
        serializer = UserRegistrationSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        
        user = serializer.save()
        self.assertIsInstance(user, User)
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
        self.assertEqual(user.bio, 'Test bio')
        self.assertEqual(user.date_of_birth, date(1990, 1, 1))
        
        # Check that password was set correctly
        self.assertTrue(user.check_password('testpass123'))


class UserProfileSerializerTest(TestCase):
    """Test cases for UserProfileSerializer"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            bio='Test bio',
            date_of_birth='1990-01-01'
        )

    def test_serialize_user_profile(self):
        """Test serializing user profile"""
        serializer = UserProfileSerializer(self.user)
        data = serializer.data
        
        # Check required fields
        self.assertEqual(data['username'], 'testuser')
        self.assertEqual(data['email'], 'test@example.com')
        self.assertEqual(data['first_name'], 'Test')
        self.assertEqual(data['last_name'], 'User')
        self.assertEqual(data['bio'], 'Test bio')
        self.assertEqual(data['date_of_birth'], '1990-01-01')
        self.assertEqual(data['full_name'], 'Test User')
        self.assertFalse(data['is_verified'])
        
        # Check computed fields
        self.assertIn('posts_count', data)
        self.assertIn('comments_count', data)
        self.assertIn('download_count', data)
        self.assertIn('date_joined', data)

    def test_update_user_profile(self):
        """Test updating user profile"""
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'bio': 'Updated bio'
        }
        
        serializer = UserProfileSerializer(self.user, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        updated_user = serializer.save()
        self.assertEqual(updated_user.first_name, 'Updated')
        self.assertEqual(updated_user.last_name, 'Name')
        self.assertEqual(updated_user.bio, 'Updated bio')

    def test_read_only_fields_not_modifiable(self):
        """Test that read-only fields cannot be modified"""
        data = {
            'username': 'newusername',
            'email': 'newemail@example.com',
            'is_verified': True
        }
        
        serializer = UserProfileSerializer(self.user, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        updated_user = serializer.save()
        # These fields should remain unchanged
        self.assertEqual(updated_user.username, 'testuser')
        self.assertEqual(updated_user.email, 'test@example.com')
        self.assertFalse(updated_user.is_verified)

    def test_bio_length_validation(self):
        """Test bio length validation"""
        long_bio = 'a' * 501  # Exceeds 500 character limit
        data = {'bio': long_bio}
        
        serializer = UserProfileSerializer(self.user, data=data, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn('bio', serializer.errors)

    def test_serializer_fields(self):
        """Test that serializer includes all expected fields"""
        serializer = UserProfileSerializer(self.user)
        actual_fields = set(serializer.data.keys())
        
        expected_fields = {
            'id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'bio', 'avatar', 'date_of_birth', 
            'is_verified', 'date_joined', 'posts_count', 
            'comments_count', 'download_count'
        }
        
        self.assertEqual(actual_fields, expected_fields)

    def test_full_name_computation(self):
        """Test that full_name is computed correctly"""
        serializer = UserProfileSerializer(self.user)
        self.assertEqual(serializer.data['full_name'], 'Test User')
        
        # Test with no names
        self.user.first_name = ''
        self.user.last_name = ''
        self.user.save()
        
        serializer = UserProfileSerializer(self.user)
        self.assertEqual(serializer.data['full_name'], '')

    def test_posts_count_computation(self):
        """Test that posts_count is computed correctly"""
        serializer = UserProfileSerializer(self.user)
        self.assertEqual(serializer.data['posts_count'], 0)

    def test_comments_count_computation(self):
        """Test that comments_count is computed correctly"""
        serializer = UserProfileSerializer(self.user)
        self.assertEqual(serializer.data['comments_count'], 0)

    def test_download_count_field(self):
        """Test that download_count field is present"""
        serializer = UserProfileSerializer(self.user)
        self.assertIn('download_count', serializer.data)
        self.assertEqual(serializer.data['download_count'], 0)

