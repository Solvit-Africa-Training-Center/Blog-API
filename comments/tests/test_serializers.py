from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import serializers
from blog.models import BlogPost, Category
from ..models import Comment
from ..serializers import CommentSerializer, CommentCreateSerializer

User = get_user_model()

class CommentSerializerTest(TestCase):
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        
        self.other_user = User.objects.create_user(
            email='other@example.com',
            username='otheruser',
            password='otherpass123'
        )
        
        self.category = Category.objects.create(
            name='Technology',
            description='Technology related posts'
        )
        
        self.post = BlogPost.objects.create(
            title='Test Blog Post',
            content='This is a test blog post content.',
            excerpt='Test excerpt',
            author=self.user,
            category=self.category,
            is_public=True,
            status=BlogPost.PUBLISHED,
            meta_description='Test meta description',
        )
        
        self.comment = Comment.objects.create(
            content='This is a test comment content.',
            author=self.user,
            post=self.post,
        )

    def test_comment_serializer_fields(self):
        """Test comment serializer includes all expected fields"""
        serializer = CommentSerializer(self.comment)
        expected_fields = {
            'id', 'content', 'author_name', 'author_username', 'author_avatar',
            'post', 'post_title', 'parent', 'replies', 'is_approved', 'is_edited',
            'is_author', 'created_at', 'updated_at'
        }
        actual_fields = set(serializer.data.keys())
        self.assertEqual(actual_fields, expected_fields)

    def test_comment_serializer_data(self):
        """Test comment serializer data"""
        serializer = CommentSerializer(self.comment)
        data = serializer.data
        
        self.assertEqual(data['content'], self.comment.content)
        self.assertEqual(data['author_username'], self.user.username)
        self.assertEqual(data['post'], self.post.id)
        self.assertIsNone(data['parent'])
        self.assertEqual(data['is_approved'], self.comment.is_approved)
        self.assertEqual(data['is_edited'], self.comment.is_edited)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)

    def test_comment_serializer_author_field(self):
        """Test comment serializer author field"""
        serializer = CommentSerializer(self.comment)
        data = serializer.data
        
        # Author should be serialized as username
        self.assertEqual(data['author_username'], self.user.username)

    def test_comment_serializer_post_field(self):
        """Test comment serializer post field"""
        serializer = CommentSerializer(self.comment)
        data = serializer.data
        
        # Post should be serialized as id
        self.assertEqual(data['post'], self.post.id)

    def test_comment_serializer_parent_field(self):
        """Test comment serializer parent field"""
        # Create a reply comment
        reply_comment = Comment.objects.create(
            content='This is a reply comment.',
            author=self.other_user,
            post=self.post,
            parent=self.comment,
        )
        
        serializer = CommentSerializer(reply_comment)
        data = serializer.data
        
        # Parent should be serialized as id
        self.assertEqual(data['parent'], self.comment.id)

    def test_comment_serializer_nested_replies(self):
        """Test comment serializer with nested replies"""
        # Create a reply comment
        reply_comment = Comment.objects.create(
            content='This is a reply comment.',
            author=self.other_user,
            post=self.post,
            parent=self.comment,
        )
        
        # Create a nested reply
        nested_reply = Comment.objects.create(
            content='This is a nested reply.',
            author=self.user,
            post=self.post,
            parent=reply_comment,
        )
        
        # Test parent comment serializer
        parent_serializer = CommentSerializer(self.comment)
        self.assertIsNone(parent_serializer.data['parent'])
        
        # Test reply comment serializer
        reply_serializer = CommentSerializer(reply_comment)
        self.assertEqual(reply_serializer.data['parent'], self.comment.id)
        
        # Test nested reply serializer
        nested_serializer = CommentSerializer(nested_reply)
        self.assertEqual(nested_serializer.data['parent'], reply_comment.id)

    def test_comment_serializer_approval_status(self):
        """Test comment serializer approval status"""
        # Test approved comment
        serializer = CommentSerializer(self.comment)
        self.assertTrue(serializer.data['is_approved'])
        
        # Test unapproved comment
        self.comment.is_approved = False
        self.comment.save()
        
        serializer = CommentSerializer(self.comment)
        self.assertFalse(serializer.data['is_approved'])

    def test_comment_serializer_editing_status(self):
        """Test comment serializer editing status"""
        # Test unedited comment
        serializer = CommentSerializer(self.comment)
        self.assertFalse(serializer.data['is_edited'])
        
        # Test edited comment
        self.comment.content = 'Updated comment content'
        self.comment.save()
        
        serializer = CommentSerializer(self.comment)
        self.assertTrue(serializer.data['is_edited'])

    def test_comment_serializer_timestamps(self):
        """Test comment serializer timestamps"""
        serializer = CommentSerializer(self.comment)
        data = serializer.data
        
        # Timestamps should be present
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
        
        # Timestamps should be strings (serialized)
        self.assertIsInstance(data['created_at'], str)
        self.assertIsInstance(data['updated_at'], str)


class CommentCreateSerializerTest(TestCase):
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        
        self.other_user = User.objects.create_user(
            email='other@example.com',
            username='otheruser',
            password='otherpass123'
        )
        
        self.category = Category.objects.create(
            name='Technology',
            description='Technology related posts'
        )
        
        self.post = BlogPost.objects.create(
            title='Test Blog Post',
            content='This is a test blog post content.',
            excerpt='Test excerpt',
            author=self.user,
            category=self.category,
            is_public=True,
            status=BlogPost.PUBLISHED,
            meta_description='Test meta description',
        )
        
        self.comment = Comment.objects.create(
            content='This is a test comment content.',
            author=self.user,
            post=self.post,
        )

    def test_comment_create_update_serializer_fields(self):
        """Test comment create/update serializer includes expected fields"""
        serializer = CommentCreateSerializer(self.comment)
        expected_fields = {
            'content', 'post', 'parent'
        }
        actual_fields = set(serializer.data.keys())
        self.assertEqual(actual_fields, expected_fields)

    def test_comment_create_update_serializer_create(self):
        """Test comment create/update serializer create method"""
        new_comment_data = {
            'content': 'This is a new comment content.',
            'post': self.post.id,
        }
        
        # Create a mock request context
        mock_request = type('Request', (), {'user': self.user})()
        serializer = CommentCreateSerializer(data=new_comment_data, context={'request': mock_request})
        self.assertTrue(serializer.is_valid())
        
        comment = serializer.save()
        self.assertEqual(comment.content, new_comment_data['content'])
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.post, self.post)

    def test_comment_create_update_serializer_create_with_parent(self):
        """Test comment create/update serializer create method with parent"""
        new_comment_data = {
            'content': 'This is a reply comment content.',
            'post': self.post.id,
            'parent': self.comment.id,
        }
        
        # Create a mock request context
        mock_request = type('Request', (), {'user': self.other_user})()
        serializer = CommentCreateSerializer(data=new_comment_data, context={'request': mock_request})
        self.assertTrue(serializer.is_valid())
        
        comment = serializer.save()
        self.assertEqual(comment.content, new_comment_data['content'])
        self.assertEqual(comment.parent, self.comment)
        self.assertEqual(comment.author, self.other_user)

    def test_comment_create_update_serializer_update(self):
        """Test comment create/update serializer update method"""
        update_data = {
            'content': 'This is updated comment content.',
        }
        
        serializer = CommentCreateSerializer(self.comment, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        updated_comment = serializer.save()
        self.assertEqual(updated_comment.content, update_data['content'])

    def test_comment_create_update_serializer_validation(self):
        """Test comment create/update serializer validation"""
        # Test required fields
        invalid_data = {}
        serializer = CommentCreateSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('content', serializer.errors)
        self.assertIn('post', serializer.errors)

        # Test content length
        long_content_data = {
            'content': 'a' * 1001,  # Exceeds max_length
            'post': self.post.id,
        }
        serializer = CommentCreateSerializer(data=long_content_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('content', serializer.errors)

    def test_comment_create_update_serializer_author_field(self):
        """Test comment create/update serializer author field handling"""
        serializer = CommentCreateSerializer(self.comment)
        data = serializer.data
        
        # Author should not be included in create serializer
        self.assertNotIn('author_username', data)

    def test_comment_create_update_serializer_post_field(self):
        """Test comment create/update serializer post field handling"""
        serializer = CommentCreateSerializer(self.comment)
        data = serializer.data
        
        # Post should be serialized as id for updates
        self.assertEqual(data['post'], self.post.id)

    def test_comment_create_update_serializer_parent_field(self):
        """Test comment create/update serializer parent field handling"""
        # Create a reply comment
        reply_comment = Comment.objects.create(
            content='This is a reply comment.',
            author=self.other_user,
            post=self.post,
            parent=self.comment,
        )
        
        serializer = CommentCreateSerializer(reply_comment)
        data = serializer.data
        
        # Parent should be serialized as id for updates
        self.assertEqual(data['parent'], self.comment.id)

    def test_comment_create_update_serializer_approval_field(self):
        """Test comment create/update serializer approval field"""
        serializer = CommentCreateSerializer(self.comment)
        data = serializer.data
        
        # is_approved should not be included in create serializer
        self.assertNotIn('is_approved', data)

    def test_comment_create_update_serializer_editing_field(self):
        """Test comment create/update serializer editing field"""
        serializer = CommentCreateSerializer(self.comment)
        data = serializer.data
        
        # is_edited should not be included in create serializer
        self.assertNotIn('is_edited', data)

    def test_comment_create_update_serializer_timestamps(self):
        """Test comment create/update serializer timestamps"""
        serializer = CommentCreateSerializer(self.comment)
        data = serializer.data
        
        # Timestamps should not be included in create serializer
        self.assertNotIn('created_at', data)
        self.assertNotIn('updated_at', data)

    def test_comment_create_update_serializer_context_required(self):
        """Test comment create/update serializer requires context for create"""
        new_comment_data = {
            'content': 'This is a new comment content.',
            'post': self.post.id,
        }
        
        # Without context, validation works but save will raise KeyError
        serializer = CommentCreateSerializer(data=new_comment_data)
        self.assertTrue(serializer.is_valid())
        with self.assertRaises(KeyError):
            serializer.save()
        
        # With context, save succeeds
        mock_request = type('Request', (), {'user': self.user})()
        serializer = CommentCreateSerializer(data=new_comment_data, context={'request': mock_request})
        self.assertTrue(serializer.is_valid())
        comment = serializer.save()
        self.assertEqual(comment.author, self.user)

    def test_comment_create_update_serializer_partial_update(self):
        """Test comment create/update serializer partial update"""
        update_data = {
            'content': 'This is a partial update.',
        }
        
        serializer = CommentCreateSerializer(self.comment, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        updated_comment = serializer.save()
        self.assertEqual(updated_comment.content, update_data['content'])
        
        # Other fields should remain unchanged
        self.assertEqual(updated_comment.author, self.user)
        self.assertEqual(updated_comment.post, self.post)

    def test_comment_create_update_serializer_full_update(self):
        """Test comment create/update serializer full update"""
        update_data = {
            'content': 'This is a full update.',
            'post': self.post.id,
        }
        
        serializer = CommentCreateSerializer(self.comment, data=update_data)
        self.assertTrue(serializer.is_valid())
        
        updated_comment = serializer.save()
        self.assertEqual(updated_comment.content, update_data['content'])
        self.assertEqual(updated_comment.post, self.post)

    def test_comment_create_update_serializer_invalid_post(self):
        """Test comment create/update serializer with invalid post"""
        invalid_data = {
            'content': 'This is a comment with invalid post.',
            'post': 99999,  # Non-existent post ID
        }
        
        serializer = CommentCreateSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('post', serializer.errors)

    def test_comment_create_update_serializer_invalid_parent(self):
        """Test comment create/update serializer with invalid parent"""
        invalid_data = {
            'content': 'This is a comment with invalid parent.',
            'post': self.post.id,
            'parent': 99999,  # Non-existent comment ID
        }
        
        serializer = CommentCreateSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('parent', serializer.errors)

