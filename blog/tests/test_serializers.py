from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import serializers
from blog.serializers import (
    CategorySerializer, TagSerializer, BlogPostListSerializer,
    BlogPostDetailSerializer, BlogPostCreateUpdateSerializer
)
from blog.models import Category, Tag, BlogPost
import tempfile
import os
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()


class CategorySerializerTest(TestCase):
    """Test cases for CategorySerializer"""

    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(
            name='Technology',
            description='Technology related posts',
            slug='technology'
        )

    def test_category_serializer_fields(self):
        """Test that CategorySerializer includes all expected fields"""
        serializer = CategorySerializer(self.category)
        actual_fields = set(serializer.data.keys())
        
        expected_fields = {
            'id', 'name', 'description', 'slug', 'posts_count', 'created_at'
        }
        
        self.assertEqual(actual_fields, expected_fields)

    def test_category_serializer_data(self):
        """Test that CategorySerializer correctly serializes data"""
        serializer = CategorySerializer(self.category)
        data = serializer.data
        
        self.assertEqual(data['name'], 'Technology')
        self.assertEqual(data['description'], 'Technology related posts')
        self.assertEqual(data['slug'], 'technology')
        self.assertEqual(data['posts_count'], 0)
        self.assertIn('created_at', data)

    def test_category_serializer_posts_count(self):
        """Test that posts_count is computed correctly"""
        # Create a user and blog post
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        post = BlogPost.objects.create(
            title='Test Post',
            slug='test-post',
            content='Test content',
            author=user,
            category=self.category,
            status='published',
            is_public=True
        )
        
        serializer = CategorySerializer(self.category)
        self.assertEqual(serializer.data['posts_count'], 1)

    def test_category_serializer_read_only_fields(self):
        """Test that read-only fields cannot be modified"""
        data = {
            'name': 'Updated Technology',
            'description': 'Updated description',
            'slug': 'updated-slug'
        }
        
        serializer = CategorySerializer(self.category, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        # Slug should remain unchanged as it's read-only
        updated_category = serializer.save()
        self.assertEqual(updated_category.slug, 'technology')  # Original slug


class TagSerializerTest(TestCase):
    """Test cases for TagSerializer"""

    def setUp(self):
        """Set up test data"""
        self.tag = Tag.objects.create(
            name='Python',
            slug='python'
        )

    def test_tag_serializer_fields(self):
        """Test that TagSerializer includes all expected fields"""
        serializer = TagSerializer(self.tag)
        actual_fields = set(serializer.data.keys())
        
        expected_fields = {
            'id', 'name', 'slug', 'posts_count', 'created_at'
        }
        
        self.assertEqual(actual_fields, expected_fields)

    def test_tag_serializer_data(self):
        """Test that TagSerializer correctly serializes data"""
        serializer = TagSerializer(self.tag)
        data = serializer.data
        
        self.assertEqual(data['name'], 'Python')
        self.assertEqual(data['slug'], 'python')
        self.assertEqual(data['posts_count'], 0)
        self.assertIn('created_at', data)

    def test_tag_serializer_posts_count(self):
        """Test that posts_count is computed correctly"""
        # Create a user, category, and blog post
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        category = Category.objects.create(
            name='Technology',
            description='Technology related posts',
            slug='technology'
        )
        
        post = BlogPost.objects.create(
            title='Test Post',
            slug='test-post',
            content='Test content',
            author=user,
            category=category,
            status='published',
            is_public=True
        )
        post.tags.add(self.tag)
        
        serializer = TagSerializer(self.tag)
        self.assertEqual(serializer.data['posts_count'], 1)


class BlogPostListSerializerTest(TestCase):
    """Test cases for BlogPostListSerializer"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.category = Category.objects.create(
            name='Technology',
            description='Technology related posts',
            slug='technology'
        )
        
        self.tag = Tag.objects.create(
            name='Python',
            slug='python'
        )
        
        self.post = BlogPost.objects.create(
            title='Test Blog Post',
            slug='test-blog-post',
            content='This is a test blog post content that should be long enough to generate an excerpt.',
            excerpt='This is a test blog post content...',
            author=self.user,
            category=self.category,
            status='published',
            is_public=True
        )
        self.post.tags.add(self.tag)

    def test_blog_post_list_serializer_fields(self):
        """Test that BlogPostListSerializer includes expected fields"""
        serializer = BlogPostListSerializer(self.post)
        actual_fields = set(serializer.data.keys())
        
        expected_fields = {
            'id', 'title', 'slug', 'excerpt', 'author_name', 'author_username',
            'category_name', 'tags', 'is_public', 'status', 'featured_image',
            'publication_date', 'created_at', 'view_count', 'like_count',
            'comments_count', 'reading_time'
        }
        
        self.assertEqual(actual_fields, expected_fields)

    def test_blog_post_list_serializer_data(self):
        """Test that BlogPostListSerializer correctly serializes data"""
        serializer = BlogPostListSerializer(self.post)
        data = serializer.data
        
        self.assertEqual(data['title'], 'Test Blog Post')
        self.assertEqual(data['slug'], 'test-blog-post')
        self.assertEqual(data['excerpt'], 'This is a test blog post content...')
        self.assertEqual(data['author_name'], 'Test User')
        self.assertEqual(data['author_username'], 'testuser')
        self.assertEqual(data['category_name'], 'Technology')
        self.assertEqual(data['status'], 'published')
        self.assertTrue(data['is_public'])
        self.assertEqual(data['view_count'], 0)
        self.assertEqual(data['like_count'], 0)
        self.assertEqual(data['comments_count'], 0)

    def test_blog_post_list_serializer_author_field(self):
        """Test blog post list serializer author field"""
        serializer = BlogPostListSerializer(self.post)
        self.assertEqual(serializer.data['author_name'], 'Test User')
        self.assertEqual(serializer.data['author_username'], 'testuser')

    def test_blog_post_list_serializer_category_field(self):
        """Test blog post list serializer category field"""
        serializer = BlogPostListSerializer(self.post)
        self.assertEqual(serializer.data['category_name'], 'Technology')

    def test_blog_post_list_serializer_tags_field(self):
        """Test blog post list serializer tags field"""
        serializer = BlogPostListSerializer(self.post)
        tags_data = serializer.data['tags']
        self.assertEqual(len(tags_data), 1)
        self.assertEqual(tags_data[0]['name'], 'Python')

    def test_blog_post_list_serializer_reading_time(self):
        """Test that reading_time is computed correctly"""
        serializer = BlogPostListSerializer(self.post)
        # Content has about 15 words, so reading time should be 1 minute
        self.assertEqual(serializer.data['reading_time'], 1)

    def test_blog_post_list_serializer_comments_count(self):
        """Test that comments_count is computed correctly"""
        serializer = BlogPostListSerializer(self.post)
        self.assertEqual(serializer.data['comments_count'], 0)


class BlogPostDetailSerializerTest(TestCase):
    """Test cases for BlogPostDetailSerializer"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.category = Category.objects.create(
            name='Technology',
            description='Technology related posts',
            slug='technology'
        )
        
        self.tag = Tag.objects.create(
            name='Python',
            slug='python'
        )
        
        self.post = BlogPost.objects.create(
            title='Test Blog Post',
            slug='test-blog-post',
            content='This is a test blog post content that should be long enough to generate an excerpt.',
            excerpt='This is a test blog post content...',
            author=self.user,
            category=self.category,
            status='published',
            is_public=True,
            meta_description='Test meta description'
        )
        self.post.tags.add(self.tag)

    def test_blog_post_detail_serializer_fields(self):
        """Test that BlogPostDetailSerializer includes all fields"""
        serializer = BlogPostDetailSerializer(self.post)
        actual_fields = set(serializer.data.keys())
        
        expected_fields = {
            'id', 'title', 'slug', 'content', 'excerpt', 'author',
            'category', 'tags', 'is_public', 'status', 'meta_description',
            'featured_image', 'publication_date', 'created_at', 'updated_at',
            'view_count', 'like_count', 'comments_count', 'reading_time'
        }
        
        self.assertEqual(actual_fields, expected_fields)

    def test_blog_post_detail_serializer_data(self):
        """Test that BlogPostDetailSerializer correctly serializes data"""
        serializer = BlogPostDetailSerializer(self.post)
        data = serializer.data
        
        self.assertEqual(data['title'], 'Test Blog Post')
        self.assertEqual(data['slug'], 'test-blog-post')
        self.assertEqual(data['content'], 'This is a test blog post content that should be long enough to generate an excerpt.')
        self.assertEqual(data['excerpt'], 'This is a test blog post content...')
        self.assertEqual(data['status'], 'published')
        self.assertTrue(data['is_public'])
        self.assertEqual(data['meta_description'], 'Test meta description')
        self.assertEqual(data['view_count'], 0)
        self.assertEqual(data['like_count'], 0)
        self.assertEqual(data['comments_count'], 0)

    def test_blog_post_detail_serializer_author_field(self):
        """Test blog post detail serializer author field"""
        serializer = BlogPostDetailSerializer(self.post)
        author_data = serializer.data['author']
        self.assertEqual(author_data['username'], 'testuser')
        self.assertEqual(author_data['full_name'], 'Test User')

    def test_blog_post_detail_serializer_category_field(self):
        """Test blog post detail serializer category field"""
        serializer = BlogPostDetailSerializer(self.post)
        category_data = serializer.data['category']
        self.assertEqual(category_data['name'], 'Technology')
        self.assertEqual(category_data['description'], 'Technology related posts')

    def test_blog_post_detail_serializer_tags_field(self):
        """Test blog post detail serializer tags field"""
        serializer = BlogPostDetailSerializer(self.post)
        tags_data = serializer.data['tags']
        self.assertEqual(len(tags_data), 1)
        self.assertEqual(tags_data[0]['name'], 'Python')

    def test_blog_post_detail_serializer_read_only_fields(self):
        """Test that read-only fields are present but not modifiable"""
        serializer = BlogPostDetailSerializer(self.post)
        data = serializer.data
        
        # These fields should be present
        self.assertIn('slug', data)
        self.assertIn('view_count', data)
        self.assertIn('like_count', data)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)


class BlogPostCreateUpdateSerializerTest(TestCase):
    """Test cases for BlogPostCreateUpdateSerializer"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        self.category = Category.objects.create(name='Technology', description='Technology related posts', slug='technology')
        self.tag = Tag.objects.create(name='Python', slug='python')
        self.post = BlogPost.objects.create(
            title='Test Blog Post', slug='test-blog-post',
            content='This is a test blog post content that should be long enough to meet the minimum requirement. '*3,
            excerpt='This is a test blog post content...', author=self.user, category=self.category,
            status='published', is_public=True
        )
        self.post.tags.add(self.tag)

    def test_blog_post_create_update_serializer_fields(self):
        """Test that BlogPostCreateUpdateSerializer includes expected fields"""
        serializer = BlogPostCreateUpdateSerializer()
        actual_fields = set(serializer.fields.keys())
        
        expected_fields = {
            'title', 'content', 'excerpt', 'category', 'tags',
            'is_public', 'status', 'meta_description', 'featured_image'
        }
        
        self.assertEqual(actual_fields, expected_fields)

    def test_blog_post_create_update_serializer_valid_data(self):
        data = {
            'title': 'New Blog Post',
            'content': 'This is a new blog post content that meets the minimum length requirement. '*3,
            'excerpt': 'New blog post excerpt',
            'category': self.category.id,
            'tags': [self.tag.id],
            'is_public': True,
            'status': 'draft'
        }
        serializer = BlogPostCreateUpdateSerializer(data=data, context={'request': type('Request', (), {'user': self.user})()})
        self.assertTrue(serializer.is_valid())

    def test_blog_post_create_update_serializer_missing_title(self):
        """Test that BlogPostCreateUpdateSerializer requires title"""
        data = {
            'content': 'This is a blog post content without title.',
            'category': self.category.id
        }
        
        serializer = BlogPostCreateUpdateSerializer(data=data, context={'request': type('Request', (), {'user': self.user})()})
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)

    def test_blog_post_create_update_serializer_missing_content(self):
        """Test that BlogPostCreateUpdateSerializer requires content"""
        data = {
            'title': 'Blog Post Without Content',
            'category': self.category.id
        }
        
        serializer = BlogPostCreateUpdateSerializer(data=data, context={'request': type('Request', (), {'user': self.user})()})
        self.assertFalse(serializer.is_valid())
        self.assertIn('content', serializer.errors)

    def test_blog_post_create_update_serializer_title_too_short(self):
        """Test that BlogPostCreateUpdateSerializer validates title length"""
        data = {
            'title': 'Hi',  # Too short
            'content': 'This is a blog post content that meets the minimum length requirement.',
            'category': self.category.id
        }
        
        serializer = BlogPostCreateUpdateSerializer(data=data, context={'request': type('Request', (), {'user': self.user})()})
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)

    def test_blog_post_create_update_serializer_content_too_short(self):
        """Test that BlogPostCreateUpdateSerializer validates content length"""
        data = {
            'title': 'Valid Title',
            'content': 'Short',  # Too short
            'category': self.category.id
        }
        
        serializer = BlogPostCreateUpdateSerializer(data=data, context={'request': type('Request', (), {'user': self.user})()})
        self.assertFalse(serializer.is_valid())
        self.assertIn('content', serializer.errors)

    def test_blog_post_create_update_serializer_too_many_tags(self):
        """Test that BlogPostCreateUpdateSerializer validates tag count"""
        # Create many tags
        tags = []
        for i in range(11):
            tag = Tag.objects.create(name=f'Tag{i}', slug=f'tag{i}')
            tags.append(tag.id)
        
        data = {
            'title': 'Valid Title',
            'content': 'This is a blog post content that meets the minimum length requirement.',
            'category': self.category.id,
            'tags': tags  # Too many tags
        }
        
        serializer = BlogPostCreateUpdateSerializer(data=data, context={'request': type('Request', (), {'user': self.user})()})
        self.assertFalse(serializer.is_valid())
        self.assertIn('tags', serializer.errors)

    def test_blog_post_create_update_serializer_create(self):
        data = {
            'title': 'New Blog Post',
            'content': 'This is a new blog post content that meets the minimum length requirement. '*3,
            'excerpt': 'New blog post excerpt',
            'category': self.category.id,
            'tags': [self.tag.id],
            'is_public': True,
            'status': 'draft'
        }
        serializer = BlogPostCreateUpdateSerializer(data=data, context={'request': type('Request', (), {'user': self.user})()})
        self.assertTrue(serializer.is_valid())
        post = serializer.save()
        self.assertEqual(post.title, 'New Blog Post')
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.category, self.category)
        self.assertEqual(list(post.tags.all()), [self.tag])

    def test_blog_post_create_update_serializer_update(self):
        data = {'title': 'Updated Blog Post', 'content': 'This is an updated blog post content that meets the minimum length requirement. '*3}
        serializer = BlogPostCreateUpdateSerializer(self.post, data=data, partial=True, context={'request': type('Request', (), {'user': self.user})()})
        self.assertTrue(serializer.is_valid())
        updated_post = serializer.save()
        self.assertEqual(updated_post.title, 'Updated Blog Post')
        self.assertIn('meets the minimum', updated_post.content)

    def test_blog_post_create_update_serializer_author_field(self):
        data = {'title': 'New Blog Post', 'content': 'This is a new blog post content that meets the minimum length requirement. '*3, 'category': self.category.id}
        serializer = BlogPostCreateUpdateSerializer(data=data, context={'request': type('Request', (), {'user': self.user})()})
        self.assertTrue(serializer.is_valid())
        post = serializer.save()
        self.assertEqual(post.author, self.user)

    def test_blog_post_create_update_serializer_with_featured_image(self):
        # Create a temporary image file and wrap in SimpleUploadedFile
        temp_image = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        img = Image.new('RGB', (100, 100), color='red')
        img.save(temp_image.name)
        temp_image.close()
        try:
            with open(temp_image.name, 'rb') as f:
                image_bytes = f.read()
            uploaded = SimpleUploadedFile('test.jpg', image_bytes, content_type='image/jpeg')
            data = {
                'title': 'Blog Post with Image',
                'content': 'This is a blog post content that meets the minimum length requirement. '*3,
                'category': self.category.id,
                'featured_image': uploaded
            }
            serializer = BlogPostCreateUpdateSerializer(data=data, context={'request': type('Request', (), {'user': self.user})()})
            self.assertTrue(serializer.is_valid(), serializer.errors)
            post = serializer.save()
            self.assertEqual(post.title, 'Blog Post with Image')
        finally:
            if os.path.exists(temp_image.name):
                os.unlink(temp_image.name)

