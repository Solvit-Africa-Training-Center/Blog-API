# ===== blog/models.py =====
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from django.utils.text import slugify

class Category(models.Model):
    """
    Categories for organizing blog posts
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Tag(models.Model):
    """
    Tags for labeling blog posts
    """
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class BlogPost(models.Model):
    """
    Main blog post model with all required features
    """
    DRAFT = 'draft'
    PUBLISHED = 'published'
    ARCHIVED = 'archived'
    
    STATUS_CHOICES = [
        (DRAFT, 'Draft'),
        (PUBLISHED, 'Published'),
        (ARCHIVED, 'Archived'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    content = models.TextField()
    excerpt = models.TextField(max_length=300, blank=True, help_text="Brief description of the post")
    
    # Relationships
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='blog_posts'
    )
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='posts'
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name='posts')
    
    # Visibility and status
    is_public = models.BooleanField(
        default=True, 
        help_text="Public posts are visible to all authenticated users"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=DRAFT)
    
    # SEO and metadata
    meta_description = models.CharField(max_length=160, blank=True)
    featured_image = models.ImageField(upload_to='blog/images/', null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    publication_date = models.DateTimeField(null=True, blank=True)
    
    # Engagement metrics
    view_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'is_public']),
            models.Index(fields=['publication_date']),
            models.Index(fields=['author', 'created_at']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Auto-generate slug from title
        if not self.slug:
            self.slug = slugify(self.title)
        
        # Set publication date when status changes to published
        if self.status == self.PUBLISHED and not self.publication_date:
            self.publication_date = timezone.now()
        
        # Generate excerpt from content if not provided
        if not self.excerpt and self.content:
            self.excerpt = self.content[:297] + "..."
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('blog:posts-detail', kwargs={'pk': self.pk})
    
    def is_published(self):
        return self.status == self.PUBLISHED
    
    def can_be_viewed_by(self, user):
        """Check if a user can view this post"""
        if not user.is_authenticated:
            return False
        
        # Authors can always view their own posts
        if self.author == user:
            return True
        
        # Public published posts can be viewed by any authenticated user
        if self.is_public and self.status == self.PUBLISHED:
            return True
        
        return False
    
    def increment_view_count(self):
        """Increment view count"""
        self.view_count += 1
        self.save(update_fields=['view_count'])