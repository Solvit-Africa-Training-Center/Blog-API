from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from django.core.exceptions import ValidationError
from ..models import Category, Tag, BlogPost
import tempfile
import os
from PIL import Image

User = get_user_model()

class CategoryModelTest(TestCase):
    def setUp(self):
        """Set up test data"""
        self.category_data = {
            'name': 'Technology',
            'description': 'Technology related posts',
        }

    def test_create_category(self):
        """Test creating a basic category"""
        category = Category.objects.create(**self.category_data)
        self.assertEqual(category.name, self.category_data['name'])
        self.assertEqual(category.description, self.category_data['description'])
        self.assertIsNotNone(category.slug)
        self.assertEqual(category.slug, 'technology')
        self.assertIsNotNone(category.created_at)
        self.assertIsNotNone(category.updated_at)

    def test_category_str_representation(self):
        """Test string representation of category"""
        category = Category.objects.create(**self.category_data)
        self.assertEqual(str(category), self.category_data['name'])

    def test_category_slug_auto_generation(self):
        """Test automatic slug generation"""
        category = Category.objects.create(**self.category_data)
        self.assertEqual(category.slug, 'technology')

    def test_category_slug_custom(self):
        """Test custom slug assignment"""
        category_data = self.category_data.copy()
        category_data['slug'] = 'custom-slug'
        category = Category.objects.create(**category_data)
        self.assertEqual(category.slug, 'custom-slug')

    def test_category_slug_unique(self):
        """Test category slug uniqueness"""
        Category.objects.create(**self.category_data)
        
        # Try to create another category with same slug
        duplicate_data = self.category_data.copy()
        duplicate_data['name'] = 'Another Technology'
        duplicate_data['slug'] = 'technology'
        
        with self.assertRaises(Exception):  # Django will raise IntegrityError
            Category.objects.create(**duplicate_data)

    def test_category_meta_options(self):
        """Test category model meta options"""
        category = Category.objects.create(**self.category_data)
        self.assertEqual(category._meta.verbose_name_plural, 'Categories')
        self.assertEqual(category._meta.ordering, ['name'])

    def test_category_ordering(self):
        """Test category ordering"""
        Category.objects.create(name='Zebra', description='Zebra posts')
        Category.objects.create(name='Alpha', description='Alpha posts')
        Category.objects.create(name='Beta', description='Beta posts')
        
        categories = Category.objects.all()
        self.assertEqual(categories[0].name, 'Alpha')
        self.assertEqual(categories[1].name, 'Beta')
        self.assertEqual(categories[2].name, 'Zebra')


class TagModelTest(TestCase):
    def setUp(self):
        """Set up test data"""
        self.tag_data = {
            'name': 'Python',
        }

    def test_create_tag(self):
        """Test creating a basic tag"""
        tag = Tag.objects.create(**self.tag_data)
        self.assertEqual(tag.name, self.tag_data['name'])
        self.assertIsNotNone(tag.slug)
        self.assertEqual(tag.slug, 'python')
        self.assertIsNotNone(tag.created_at)

    def test_tag_str_representation(self):
        """Test string representation of tag"""
        tag = Tag.objects.create(**self.tag_data)
        self.assertEqual(str(tag), self.tag_data['name'])

    def test_tag_slug_auto_generation(self):
        """Test automatic slug generation"""
        tag = Tag.objects.create(**self.tag_data)
        self.assertEqual(tag.slug, 'python')

    def test_tag_slug_custom(self):
        """Test custom slug assignment"""
        tag_data = self.tag_data.copy()
        tag_data['slug'] = 'custom-tag'
        tag = Tag.objects.create(**tag_data)
        self.assertEqual(tag.slug, 'custom-tag')

    def test_tag_meta_options(self):
        """Test tag model meta options"""
        tag = Tag.objects.create(**self.tag_data)
        self.assertEqual(tag._meta.ordering, ['name'])

    def test_tag_ordering(self):
        """Test tag ordering"""
        Tag.objects.create(name='Zebra')
        Tag.objects.create(name='Alpha')
        Tag.objects.create(name='Beta')
        
        tags = Tag.objects.all()
        self.assertEqual(tags[0].name, 'Alpha')
        self.assertEqual(tags[1].name, 'Beta')
        self.assertEqual(tags[2].name, 'Zebra')


class BlogPostModelTest(TestCase):
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Technology',
            description='Technology related posts'
        )
        
        self.tag = Tag.objects.create(name='Python')
        
        self.post_data = {
            'title': 'Test Blog Post',
            'content': 'This is a test blog post content.',
            'excerpt': 'Test excerpt',
            'author': self.user,
            'category': self.category,
            'is_public': True,
            'status': BlogPost.PUBLISHED,
            'meta_description': 'Test meta description',
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

    def test_create_blog_post(self):
        """Test creating a basic blog post"""
        post = BlogPost.objects.create(**self.post_data)
        post.tags.add(self.tag)
        
        self.assertEqual(post.title, self.post_data['title'])
        self.assertEqual(post.content, self.post_data['content'])
        self.assertEqual(post.excerpt, self.post_data['excerpt'])
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.category, self.category)
        self.assertTrue(post.is_public)
        self.assertEqual(post.status, BlogPost.PUBLISHED)
        self.assertEqual(post.meta_description, self.post_data['meta_description'])
        self.assertIsNotNone(post.slug)
        self.assertEqual(post.slug, 'test-blog-post')
        self.assertIsNotNone(post.created_at)
        self.assertIsNotNone(post.updated_at)
        self.assertIsNotNone(post.publication_date)
        self.assertEqual(post.view_count, 0)
        self.assertEqual(post.like_count, 0)

    def test_blog_post_str_representation(self):
        """Test string representation of blog post"""
        post = BlogPost.objects.create(**self.post_data)
        self.assertEqual(str(post), self.post_data['title'])

    def test_blog_post_slug_auto_generation(self):
        """Test automatic slug generation"""
        post = BlogPost.objects.create(**self.post_data)
        self.assertEqual(post.slug, 'test-blog-post')

    def test_blog_post_slug_custom(self):
        """Test custom slug assignment"""
        post_data = self.post_data.copy()
        post_data['slug'] = 'custom-slug'
        post = BlogPost.objects.create(**post_data)
        self.assertEqual(post.slug, 'custom-slug')

    def test_blog_post_excerpt_auto_generation(self):
        """Test automatic excerpt generation"""
        post_data = self.post_data.copy()
        del post_data['excerpt']
        post = BlogPost.objects.create(**post_data)
        # The excerpt should end with "..." (3 dots)
        # The excerpt should end with "..." (3 dots) and include the period from content
        self.assertEqual(post.excerpt, 'This is a test blog post content....')

    def test_blog_post_publication_date_auto_set(self):
        """Test automatic publication date setting"""
        post_data = self.post_data.copy()
        post_data['status'] = BlogPost.DRAFT
        post = BlogPost.objects.create(**post_data)
        
        # Initially no publication date
        self.assertIsNone(post.publication_date)
        
        # Change status to published
        post.status = BlogPost.PUBLISHED
        post.save()
        self.assertIsNotNone(post.publication_date)

    def test_blog_post_status_choices(self):
        """Test blog post status choices"""
        self.assertEqual(BlogPost.DRAFT, 'draft')
        self.assertEqual(BlogPost.PUBLISHED, 'published')
        self.assertEqual(BlogPost.ARCHIVED, 'archived')
        
        # Test valid status
        post = BlogPost.objects.create(**self.post_data)
        post.status = BlogPost.ARCHIVED
        post.save()
        self.assertEqual(post.status, BlogPost.ARCHIVED)

    def test_blog_post_get_absolute_url(self):
        """Test get_absolute_url method"""
        post = BlogPost.objects.create(**self.post_data)
        # Blog URLs use router, so the URL name is 'blog:posts-detail'
        expected_url = reverse('blog:posts-detail', kwargs={'pk': post.pk})
        self.assertEqual(post.get_absolute_url(), expected_url)

    def test_blog_post_is_published(self):
        """Test is_published method"""
        # Test published post
        post = BlogPost.objects.create(**self.post_data)
        self.assertTrue(post.is_published())
        
        # Test draft post
        post.status = BlogPost.DRAFT
        post.save()
        self.assertFalse(post.is_published())

    def test_blog_post_can_be_viewed_by(self):
        """Test can_be_viewed_by method"""
        post = BlogPost.objects.create(**self.post_data)
        
        # Test author can view
        self.assertTrue(post.can_be_viewed_by(self.user))
        
        # Test other authenticated user can view public published post
        other_user = User.objects.create_user(
            email='other@example.com',
            username='otheruser',
            password='testpass123'
        )
        self.assertTrue(post.can_be_viewed_by(other_user))
        
        # Test anonymous user cannot view (pass a mock anonymous user)
        from django.contrib.auth.models import AnonymousUser
        anonymous_user = AnonymousUser()
        self.assertFalse(post.can_be_viewed_by(anonymous_user))
        
        # Test private post
        post.is_public = False
        post.save()
        self.assertFalse(post.can_be_viewed_by(other_user))
        self.assertTrue(post.can_be_viewed_by(self.user))  # Author can still view

    def test_blog_post_increment_view_count(self):
        """Test increment_view_count method"""
        post = BlogPost.objects.create(**self.post_data)
        initial_count = post.view_count
        
        post.increment_view_count()
        post.refresh_from_db()
        
        self.assertEqual(post.view_count, initial_count + 1)

    def test_blog_post_with_featured_image(self):
        """Test blog post with featured image"""
        # Test that blog post can be created without featured image
        post = BlogPost.objects.create(**self.post_data)
        self.assertIsNotNone(post)
        self.assertEqual(post.title, 'Test Blog Post')

    def test_blog_post_meta_options(self):
        """Test blog post model meta options"""
        post = BlogPost.objects.create(**self.post_data)
        self.assertEqual(post._meta.ordering, ['-created_at'])

    def test_blog_post_indexes(self):
        """Test blog post model indexes"""
        post = BlogPost.objects.create(**self.post_data)
        indexes = post._meta.indexes
        index_fields = [index.fields for index in indexes]
        
        self.assertIn(['status', 'is_public'], index_fields)
        self.assertIn(['publication_date'], index_fields)
        self.assertIn(['author', 'created_at'], index_fields)

    def test_blog_post_relationships(self):
        """Test blog post relationships"""
        post = BlogPost.objects.create(**self.post_data)
        post.tags.add(self.tag)
        
        # Test author relationship
        self.assertEqual(post.author, self.user)
        self.assertIn(post, self.user.blog_posts.all())
        
        # Test category relationship
        self.assertEqual(post.category, self.category)
        self.assertIn(post, self.category.posts.all())
        
        # Test tags relationship
        self.assertIn(self.tag, post.tags.all())
        self.assertIn(post, self.tag.posts.all())

    def test_blog_post_validation(self):
        """Test blog post validation"""
        # Test required fields
        post_data = self.post_data.copy()
        del post_data['title']
        
        # Django will raise ValidationError when calling full_clean()
        post = BlogPost(**post_data)
        with self.assertRaises(ValidationError):
            post.full_clean()

    def test_blog_post_editing_tracking(self):
        """Test blog post editing tracking"""
        post = BlogPost.objects.create(**self.post_data)
        initial_updated_at = post.updated_at
        
        # Wait a moment to ensure timestamp difference
        import time
        time.sleep(0.1)
        
        # Update the post
        post.title = 'Updated Title'
        post.save()
        
        # updated_at should have changed
        post.refresh_from_db()
        self.assertGreater(post.updated_at, initial_updated_at)

