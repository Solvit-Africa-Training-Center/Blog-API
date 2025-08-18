from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from blog.models import BlogPost, Category
from ..models import Comment

User = get_user_model()

class CommentModelTest(TestCase):
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
        
        self.comment_data = {
            'content': 'This is a test comment content.',
            'author': self.user,
            'post': self.post,
        }

    def test_create_comment(self):
        """Test creating a basic comment"""
        comment = Comment.objects.create(**self.comment_data)
        
        self.assertEqual(comment.content, self.comment_data['content'])
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.post, self.post)
        self.assertIsNone(comment.parent)
        self.assertTrue(comment.is_approved)
        self.assertFalse(comment.is_edited)
        self.assertIsNotNone(comment.created_at)
        self.assertIsNotNone(comment.updated_at)

    def test_comment_str_representation(self):
        """Test string representation of comment"""
        comment = Comment.objects.create(**self.comment_data)
        expected_str = f"Comment by {self.user.username} on {self.post.title}"
        self.assertEqual(str(comment), expected_str)

    def test_comment_meta_options(self):
        """Test comment model meta options"""
        comment = Comment.objects.create(**self.comment_data)
        self.assertEqual(comment._meta.ordering, ['created_at'])

    def test_comment_indexes(self):
        """Test comment model indexes"""
        comment = Comment.objects.create(**self.comment_data)
        indexes = comment._meta.indexes
        index_fields = [index.fields for index in indexes]
        
        self.assertIn(['post', 'created_at'], index_fields)
        self.assertIn(['author'], index_fields)

    def test_comment_relationships(self):
        """Test comment relationships"""
        comment = Comment.objects.create(**self.comment_data)
        
        # Test author relationship
        self.assertEqual(comment.author, self.user)
        self.assertIn(comment, self.user.comments.all())
        
        # Test post relationship
        self.assertEqual(comment.post, self.post)
        self.assertIn(comment, self.post.comments.all())

    def test_comment_parent_relationship(self):
        """Test comment parent relationship for replies"""
        parent_comment = Comment.objects.create(**self.comment_data)
        
        reply_data = self.comment_data.copy()
        reply_data['parent'] = parent_comment
        reply_data['author'] = self.other_user
        
        reply_comment = Comment.objects.create(**reply_data)
        
        # Test parent relationship
        self.assertEqual(reply_comment.parent, parent_comment)
        self.assertIn(reply_comment, parent_comment.replies.all())

    def test_comment_is_reply_method(self):
        """Test is_reply method"""
        parent_comment = Comment.objects.create(**self.comment_data)
        
        reply_data = self.comment_data.copy()
        reply_data['parent'] = parent_comment
        reply_data['author'] = self.other_user
        
        reply_comment = Comment.objects.create(**reply_data)
        
        # Test is_reply method
        self.assertFalse(parent_comment.is_reply())
        self.assertTrue(reply_comment.is_reply())

    def test_comment_get_replies_method(self):
        """Test get_replies method"""
        parent_comment = Comment.objects.create(**self.comment_data)
        
        reply1_data = self.comment_data.copy()
        reply1_data['parent'] = parent_comment
        reply1_data['author'] = self.other_user
        reply1_data['content'] = 'First reply'
        
        reply2_data = self.comment_data.copy()
        reply2_data['parent'] = parent_comment
        reply2_data['author'] = self.other_user
        reply2_data['content'] = 'Second reply'
        
        reply1 = Comment.objects.create(**reply1_data)
        reply2 = Comment.objects.create(**reply2_data)
        
        # Test get_replies method
        replies = parent_comment.get_replies()
        self.assertEqual(replies.count(), 2)
        self.assertIn(reply1, replies)
        self.assertIn(reply2, replies)

    def test_comment_editing_tracking(self):
        """Test comment editing tracking"""
        comment = Comment.objects.create(**self.comment_data)
        initial_updated_at = comment.updated_at
        
        # Ensure time difference
        import time
        time.sleep(0.1)
        
        # Update the comment
        comment.content = 'Updated comment content'
        comment.save()
        
        # is_edited should be True and updated_at should have changed
        comment.refresh_from_db()
        self.assertTrue(comment.is_edited)
        self.assertGreater(comment.updated_at, initial_updated_at)

    def test_comment_editing_tracking_new_comment(self):
        """Test comment editing tracking for new comments"""
        comment = Comment.objects.create(**self.comment_data)
        
        # New comments should not be marked as edited
        self.assertFalse(comment.is_edited)

    def test_comment_editing_tracking_no_change(self):
        """Test comment editing tracking when no content change"""
        comment = Comment.objects.create(**self.comment_data)
        initial_updated_at = comment.updated_at
        
        # Update without changing content
        comment.is_approved = False
        comment.save()
        
        # is_edited should remain False
        self.assertFalse(comment.is_edited)

    def test_comment_validation(self):
        """Test comment validation"""
        # Test required fields
        invalid_data = {}
        
        with self.assertRaises(Exception):  # Django will raise IntegrityError
            Comment.objects.create(**invalid_data)

    def test_comment_content_length(self):
        """TextField max_length isn't strictly validated by full_clean; ensure long content is stored."""
        long_content = 'a' * 1001
        comment = Comment(content=long_content, author=self.user, post=self.post)
        # Should not raise ValidationError for TextField
        comment.full_clean()
        comment.save()
        self.assertEqual(Comment.objects.get(pk=comment.pk).content, long_content)

    def test_comment_ordering(self):
        """Test comment ordering by creation time"""
        # Create comments with different timestamps
        comment1 = Comment.objects.create(**self.comment_data)
        
        # Simulate time delay
        import time
        time.sleep(0.001)
        
        comment2_data = self.comment_data.copy()
        comment2_data['content'] = 'Second comment'
        comment2_data['author'] = self.other_user
        comment2 = Comment.objects.create(**comment2_data)
        
        # Test ordering
        comments = Comment.objects.all()
        self.assertEqual(comments[0], comment1)
        self.assertEqual(comments[1], comment2)

    def test_comment_threading(self):
        """Test comment threading functionality"""
        # Create parent comment
        parent_comment = Comment.objects.create(**self.comment_data)
        
        # Create first level reply
        reply1_data = self.comment_data.copy()
        reply1_data['parent'] = parent_comment
        reply1_data['author'] = self.other_user
        reply1_data['content'] = 'First level reply'
        reply1 = Comment.objects.create(**reply1_data)
        
        # Create second level reply
        reply2_data = self.comment_data.copy()
        reply2_data['parent'] = reply1
        reply2_data['author'] = self.user
        reply2_data['content'] = 'Second level reply'
        reply2 = Comment.objects.create(**reply2_data)
        
        # Test threading relationships
        self.assertEqual(reply1.parent, parent_comment)
        self.assertEqual(reply2.parent, reply1)
        self.assertIn(reply1, parent_comment.replies.all())
        self.assertIn(reply2, reply1.replies.all())

    def test_comment_approval_status(self):
        """Test comment approval status"""
        comment = Comment.objects.create(**self.comment_data)
        
        # Test default approval status
        self.assertTrue(comment.is_approved)
        
        # Test changing approval status
        comment.is_approved = False
        comment.save()
        
        self.assertFalse(comment.is_approved)

    def test_comment_cascade_delete(self):
        """Test comment cascade delete behavior"""
        parent_comment = Comment.objects.create(**self.comment_data)
        
        reply_data = self.comment_data.copy()
        reply_data['parent'] = parent_comment
        reply_data['author'] = self.other_user
        reply_data['content'] = 'Reply comment'
        
        reply_comment = Comment.objects.create(**reply_data)
        
        # Delete parent comment
        parent_comment.delete()
        
        # Reply should also be deleted
        self.assertFalse(Comment.objects.filter(pk=reply_comment.pk).exists())

    def test_comment_post_cascade_delete(self):
        """Test comment deletion when post is deleted"""
        comment = Comment.objects.create(**self.comment_data)
        
        # Delete the post
        self.post.delete()
        
        # Comment should also be deleted
        self.assertFalse(Comment.objects.filter(pk=comment.pk).exists())

    def test_comment_user_cascade_delete(self):
        """Test comment deletion when user is deleted"""
        comment = Comment.objects.create(**self.comment_data)
        
        # Delete the user
        self.user.delete()
        
        # Comment should also be deleted
        self.assertFalse(Comment.objects.filter(pk=comment.pk).exists())

    def test_comment_creation_timestamp(self):
        """Test comment creation timestamp"""
        before_creation = timezone.now()
        
        comment = Comment.objects.create(**self.comment_data)
        
        after_creation = timezone.now()
        
        # created_at should be between before and after
        self.assertGreaterEqual(comment.created_at, before_creation)
        self.assertLessEqual(comment.created_at, after_creation)

    def test_comment_update_timestamp(self):
        """Test comment update timestamp"""
        comment = Comment.objects.create(**self.comment_data)
        initial_updated_at = comment.updated_at
        
        # Wait a bit and update
        import time
        time.sleep(0.001)
        
        comment.content = 'Updated content'
        comment.save()
        
        # updated_at should have changed
        self.assertGreater(comment.updated_at, initial_updated_at)

