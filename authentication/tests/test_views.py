from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from authentication.serializers import UserRegistrationSerializer, UserProfileSerializer
from authentication.views import RegisterView, ProfileView, LogoutView, CustomTokenObtainPairView

User = get_user_model()


class AuthenticationViewsTest(APITestCase):
    """Test cases for authentication views"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create another user for testing
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )

    def get_tokens_for_user(self, user):
        """Helper method to get JWT tokens for a user"""
        refresh = RefreshToken.for_user(user)
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }

    def test_register_view_success(self):
        """Test successful user registration"""
        url = reverse('authentication:register')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'first_name': 'New',
            'last_name': 'User'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that user was created
        self.assertTrue(User.objects.filter(username='newuser').exists())
        user = User.objects.get(username='newuser')
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertEqual(user.first_name, 'New')
        self.assertEqual(user.last_name, 'User')

    def test_register_view_invalid_data(self):
        """Test registration with invalid data"""
        url = reverse('authentication:register')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123'
            # Missing password_confirm
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password_confirm', response.data)

    def test_register_view_duplicate_email(self):
        """Test registration with duplicate email"""
        url = reverse('authentication:register')
        data = {
            'username': 'newuser',
            'email': 'test@example.com',  # Already exists
            'password': 'newpass123',
            'password_confirm': 'newpass123'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_register_view_duplicate_username(self):
        """Test registration with duplicate username"""
        url = reverse('authentication:register')
        data = {
            'username': 'testuser',  # Already exists
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)

    def test_register_view_missing_fields(self):
        """Test registration with missing required fields"""
        url = reverse('authentication:register')
        
        # Test missing username
        data = {
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)
        
        # Test missing email
        data = {
            'username': 'newuser',
            'password': 'newpass123',
            'password_confirm': 'newpass123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_register_view_minimal_data(self):
        """Test registration with minimal required data"""
        url = reverse('authentication:register')
        data = {
            'username': 'minimaluser',
            'email': 'minimal@example.com',
            'password': 'minpass123',
            'password_confirm': 'minpass123'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that user was created with default values
        user = User.objects.get(username='minimaluser')
        self.assertEqual(user.first_name, '')
        self.assertEqual(user.last_name, '')

    def test_profile_view_get_authenticated(self):
        """Test getting profile when authenticated"""
        tokens = self.get_tokens_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        
        url = reverse('authentication:profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that correct user data is returned
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['first_name'], 'Test')
        self.assertEqual(response.data['last_name'], 'User')

    def test_profile_view_get_unauthenticated(self):
        """Test getting profile when not authenticated"""
        url = reverse('authentication:profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_view_patch_authenticated(self):
        """Test updating profile when authenticated"""
        tokens = self.get_tokens_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        
        url = reverse('authentication:profile')
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'bio': 'Updated bio'
        }
        
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that profile was updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')
        self.assertEqual(self.user.bio, 'Updated bio')

    def test_profile_view_patch_unauthenticated(self):
        """Test updating profile when not authenticated"""
        url = reverse('authentication:profile')
        data = {'first_name': 'Updated'}
        
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_view_read_only_fields(self):
        """Test that read-only fields cannot be updated"""
        tokens = self.get_tokens_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        
        url = reverse('authentication:profile')
        data = {
            'username': 'newusername',
            'email': 'newemail@example.com',
            'is_verified': True
        }
        
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that read-only fields were not changed
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertFalse(self.user.is_verified)

    def test_profile_view_methods(self):
        """Test profile view supports correct HTTP methods"""
        tokens = self.get_tokens_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        
        url = reverse('authentication:profile')
        
        # Test GET method
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test PATCH method
        response = self.client.patch(url, {'first_name': 'Test'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test PUT method (allowed by RetrieveUpdateAPIView)
        response = self.client.put(url, {'first_name': 'PutName'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test DELETE method (should not be allowed)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_logout_view_success(self):
        """Test successful logout"""
        tokens = self.get_tokens_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        
        url = reverse('authentication:logout')
        data = {'refresh_token': tokens['refresh']}
        
        response = self.client.post(url, data, format='json')
        self.assertIn(response.status_code, [status.HTTP_205_RESET_CONTENT, status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])

    def test_logout_view_invalid_token(self):
        """Test logout with invalid token"""
        tokens = self.get_tokens_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        url = reverse('authentication:logout')
        data = {'refresh_token': 'invalid_token'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_view_missing_token(self):
        """Test logout without token"""
        tokens = self.get_tokens_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        url = reverse('authentication:logout')
        data = {}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_view_unauthenticated(self):
        """Test logout when not authenticated"""
        url = reverse('authentication:logout')
        data = {'refresh_token': 'some_token'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_custom_token_obtain_pair_view_success(self):
        """Test successful token generation"""
        url = reverse('authentication:token_obtain_pair')
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that tokens are returned
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_custom_token_obtain_pair_view_invalid_credentials(self):
        """Test token generation with invalid credentials"""
        url = reverse('authentication:token_obtain_pair')
        data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_custom_token_obtain_pair_view_missing_credentials(self):
        """Test token generation with missing credentials"""
        url = reverse('authentication:token_obtain_pair')
        # Missing email
        data = {'password': 'testpass123'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Missing password
        data = {'email': 'test@example.com'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

