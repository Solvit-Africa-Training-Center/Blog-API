from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from ..models import Category, Tag, BlogPost
from ..serializers import (
	BlogPostListSerializer,
	BlogPostDetailSerializer,
	BlogPostCreateUpdateSerializer,
	CategorySerializer,
	TagSerializer
)
import tempfile
import os
from PIL import Image

User = get_user_model()

class BlogViewsTest(APITestCase):
	def setUp(self):
		"""Set up test data"""
		self.client = APIClient()
		self.user = User.objects.create_user(email='test@example.com', username='testuser', password='testpass123')
		self.admin_user = User.objects.create_superuser(email='admin@example.com', username='adminuser', password='adminpass123')
		self.other_user = User.objects.create_user(email='other@example.com', username='otheruser', password='otherpass123')
		self.category = Category.objects.create(name='Technology', description='Technology related posts')
		self.category2 = Category.objects.create(name='Science', description='Science related posts')
		self.tag = Tag.objects.create(name='Python')
		self.tag2 = Tag.objects.create(name='Django')
		self.published_post = BlogPost.objects.create(
			title='Published Post', content='This is a published post content that is sufficiently long to satisfy validations. '*3,
			excerpt='Published excerpt', author=self.user, category=self.category,
			is_public=True, status=BlogPost.PUBLISHED, meta_description='Published meta description',
		)
		self.published_post.tags.add(self.tag)
		self.draft_post = BlogPost.objects.create(
			title='Draft Post', content='This is a draft post content that is also long enough to be valid. '*3,
			excerpt='Draft excerpt', author=self.user, category=self.category,
			is_public=False, status=BlogPost.DRAFT, meta_description='Draft meta description',
		)
		self.other_user_post = BlogPost.objects.create(
			title='Other User Post', content='Other user post content that is long enough. '*3,
			excerpt='Other user excerpt', author=self.other_user, category=self.category2,
			is_public=True, status=BlogPost.PUBLISHED, meta_description='Other user meta description',
		)
		# Correct router names
		self.category_list_url = reverse('blog:categories-list')
		self.category_detail_url = reverse('blog:categories-detail', kwargs={'pk': self.category.pk})
		self.tag_list_url = reverse('blog:tags-list')
		self.tag_detail_url = reverse('blog:tags-detail', kwargs={'pk': self.tag.pk})
		self.post_list_url = reverse('blog:posts-list')
		self.post_detail_url = reverse('blog:posts-detail', kwargs={'pk': self.published_post.pk})
		self.draft_post_detail_url = reverse('blog:posts-detail', kwargs={'pk': self.draft_post.pk})

	def get_auth_headers(self, user):
		refresh = RefreshToken.for_user(user)
		return {'HTTP_AUTHORIZATION': f'Bearer {refresh.access_token}'}

	def _extract_results(self, response):
		return response.data['results'] if isinstance(response.data, dict) and 'results' in response.data else response.data

	def test_category_list_view_authenticated(self):
		self.client.credentials(**self.get_auth_headers(self.user))
		response = self.client.get(self.category_list_url)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		items = self._extract_results(response)
		self.assertGreaterEqual(len(items), 2)
		names = [c['name'] for c in items]
		self.assertIn('Technology', names)
		self.assertIn('Science', names)

	def test_category_list_view_unauthenticated(self):
		response = self.client.get(self.category_list_url)
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_category_detail_view_authenticated(self):
		self.client.credentials(**self.get_auth_headers(self.user))
		response = self.client.get(self.category_detail_url)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['name'], self.category.name)
		self.assertEqual(response.data['description'], self.category.description)

	def test_category_create_view_admin_only(self):
		self.client.credentials(**self.get_auth_headers(self.user))
		resp = self.client.post(self.category_list_url, {'name': 'New Category', 'description': 'New category description'})
		self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
		self.client.credentials(**self.get_auth_headers(self.admin_user))
		resp = self.client.post(self.category_list_url, {'name': 'New Category', 'description': 'New category description'})
		self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

	def test_category_update_view_admin_only(self):
		self.client.credentials(**self.get_auth_headers(self.user))
		self.assertEqual(self.client.patch(self.category_detail_url, {'name': 'Updated Technology'}).status_code, status.HTTP_403_FORBIDDEN)
		self.client.credentials(**self.get_auth_headers(self.admin_user))
		resp = self.client.patch(self.category_detail_url, {'name': 'Updated Technology'})
		self.assertEqual(resp.status_code, status.HTTP_200_OK)
		self.assertEqual(resp.data['name'], 'Updated Technology')

	def test_category_delete_view_admin_only(self):
		self.client.credentials(**self.get_auth_headers(self.user))
		self.assertEqual(self.client.delete(self.category_detail_url).status_code, status.HTTP_403_FORBIDDEN)
		self.client.credentials(**self.get_auth_headers(self.admin_user))
		self.assertEqual(self.client.delete(self.category_detail_url).status_code, status.HTTP_204_NO_CONTENT)

	def test_tag_list_view_authenticated(self):
		self.client.credentials(**self.get_auth_headers(self.user))
		response = self.client.get(self.tag_list_url)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		items = self._extract_results(response)
		self.assertGreaterEqual(len(items), 2)
		names = [t['name'] for t in items]
		self.assertIn('Python', names)
		self.assertIn('Django', names)

	def test_tag_list_view_unauthenticated(self):
		response = self.client.get(self.tag_list_url)
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_tag_detail_view_authenticated(self):
		self.client.credentials(**self.get_auth_headers(self.user))
		response = self.client.get(self.tag_detail_url)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['name'], self.tag.name)

	def test_tag_create_view_authenticated_user(self):
		self.client.credentials(**self.get_auth_headers(self.user))
		resp = self.client.post(self.tag_list_url, {'name': 'New Tag'})
		self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
		self.assertEqual(resp.data['name'], 'New Tag')

	def test_tag_delete_view_admin_only(self):
		self.client.credentials(**self.get_auth_headers(self.user))
		self.assertEqual(self.client.delete(self.tag_detail_url).status_code, status.HTTP_403_FORBIDDEN)
		self.client.credentials(**self.get_auth_headers(self.admin_user))
		self.assertEqual(self.client.delete(self.tag_detail_url).status_code, status.HTTP_204_NO_CONTENT)

	def test_blog_post_list_view_authenticated(self):
		self.client.credentials(**self.get_auth_headers(self.user))
		response = self.client.get(self.post_list_url)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		items = self._extract_results(response)
		titles = [p['title'] for p in items]
		self.assertIn('Published Post', titles)
		self.assertIn('Draft Post', titles)
		self.assertIn('Other User Post', titles)

	def test_blog_post_list_view_unauthenticated(self):
		self.assertEqual(self.client.get(self.post_list_url).status_code, status.HTTP_401_UNAUTHORIZED)

	def test_blog_post_detail_view_authenticated(self):
		self.client.credentials(**self.get_auth_headers(self.user))
		resp = self.client.get(self.post_detail_url)
		self.assertEqual(resp.status_code, status.HTTP_200_OK)
		self.assertEqual(resp.data['title'], self.published_post.title)
		self.assertEqual(resp.data['content'], self.published_post.content)

	def test_blog_post_detail_view_own_draft(self):
		self.client.credentials(**self.get_auth_headers(self.user))
		self.assertEqual(self.client.get(self.draft_post_detail_url).status_code, status.HTTP_200_OK)

	def test_blog_post_detail_view_other_user_draft_forbidden(self):
		other_draft = BlogPost.objects.create(title='Other Draft', content='Other draft content that is long enough. '*3, author=self.other_user, status=BlogPost.DRAFT, is_public=False)
		self.client.credentials(**self.get_auth_headers(self.user))
		resp = self.client.get(reverse('blog:posts-detail', kwargs={'pk': other_draft.pk}))
		# Permission returns 403 when user cannot view
		self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

	def test_blog_post_create_view_authenticated(self):
		self.client.credentials(**self.get_auth_headers(self.user))
		new_post_data = {
			'title': 'New Blog Post',
			'content': 'This is a new blog post content that meets the minimum length requirement. '*3,
			'excerpt': 'New excerpt',
			'category': self.category.id,
			'tags': [self.tag.id],
			'is_public': True,
			'status': BlogPost.DRAFT,
			'meta_description': 'New meta description',
		}
		resp = self.client.post(self.post_list_url, new_post_data)
		self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
		self.assertEqual(resp.data['title'], new_post_data['title'])

	def test_blog_post_create_view_unauthenticated(self):
		new_post_data = {'title': 'New Blog Post', 'content': 'This is a new blog post content. '*3}
		self.assertEqual(self.client.post(self.post_list_url, new_post_data).status_code, status.HTTP_401_UNAUTHORIZED)

	def test_blog_post_update_view_author(self):
		self.client.credentials(**self.get_auth_headers(self.user))
		update_data = {'title': 'Updated Blog Post Title', 'content': 'This is updated content that is long enough. '*3}
		resp = self.client.patch(self.post_detail_url, update_data)
		self.assertEqual(resp.status_code, status.HTTP_200_OK)
		self.assertEqual(resp.data['title'], update_data['title'])
		self.assertEqual(resp.data['content'].strip(), update_data['content'].strip())

	def test_blog_post_update_view_non_author_forbidden(self):
		self.client.credentials(**self.get_auth_headers(self.other_user))
		self.assertEqual(self.client.patch(self.post_detail_url, {'title': 'Unauthorized Update'}).status_code, status.HTTP_403_FORBIDDEN)

	def test_blog_post_delete_view_author(self):
		self.client.credentials(**self.get_auth_headers(self.user))
		self.assertEqual(self.client.delete(self.post_detail_url).status_code, status.HTTP_204_NO_CONTENT)

	def test_blog_post_delete_view_non_author_forbidden(self):
		self.client.credentials(**self.get_auth_headers(self.other_user))
		self.assertEqual(self.client.delete(self.post_detail_url).status_code, status.HTTP_403_FORBIDDEN)

	def test_blog_post_filtering(self):
		self.client.credentials(**self.get_auth_headers(self.user))
		self.assertEqual(self.client.get(f"{self.post_list_url}?category={self.category.id}").status_code, status.HTTP_200_OK)
		self.assertEqual(self.client.get(f"{self.post_list_url}?status={BlogPost.PUBLISHED}").status_code, status.HTTP_200_OK)
		self.assertEqual(self.client.get(f"{self.post_list_url}?author={self.user.id}").status_code, status.HTTP_200_OK)

	def test_blog_post_search(self):
		self.client.credentials(**self.get_auth_headers(self.user))
		self.assertEqual(self.client.get(f"{self.post_list_url}?search=Published").status_code, status.HTTP_200_OK)
		self.assertEqual(self.client.get(f"{self.post_list_url}?search=content").status_code, status.HTTP_200_OK)

	def test_blog_post_ordering(self):
		self.client.credentials(**self.get_auth_headers(self.user))
		self.assertEqual(self.client.get(self.post_list_url).status_code, status.HTTP_200_OK)
		self.assertEqual(self.client.get(f"{self.post_list_url}?ordering=title").status_code, status.HTTP_200_OK)

	def test_blog_post_view_count_increment(self):
		self.client.credentials(**self.get_auth_headers(self.user))
		initial = self.published_post.view_count
		self.assertEqual(self.client.get(self.post_detail_url).status_code, status.HTTP_200_OK)
		self.published_post.refresh_from_db()
		self.assertEqual(self.published_post.view_count, initial + 1)

	def test_blog_post_methods(self):
		self.client.credentials(**self.get_auth_headers(self.user))
		self.assertEqual(self.client.get(self.post_detail_url).status_code, status.HTTP_200_OK)
		# Use valid title length for patch
		self.assertEqual(self.client.patch(self.post_detail_url, {'title': 'Valid Test Title'}).status_code, status.HTTP_200_OK)
		self.assertEqual(self.client.delete(self.post_detail_url).status_code, status.HTTP_204_NO_CONTENT)
		self.assertIn(self.client.put(self.post_detail_url, {}).status_code, (status.HTTP_404_NOT_FOUND, status.HTTP_405_METHOD_NOT_ALLOWED))

	def test_blog_post_serializer_class_selection(self):
		self.client.credentials(**self.get_auth_headers(self.user))
		self.assertEqual(self.client.get(self.post_list_url).status_code, status.HTTP_200_OK)
		self.assertEqual(self.client.get(self.post_detail_url).status_code, status.HTTP_200_OK)
		new_post_data = {'title': 'Test Post', 'content': 'Test content that is sufficiently long to pass validation. '*3}
		self.assertEqual(self.client.post(self.post_list_url, new_post_data).status_code, status.HTTP_201_CREATED)

