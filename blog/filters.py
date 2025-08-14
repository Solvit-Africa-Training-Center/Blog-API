# ===== blog/filters.py =====
import django_filters
from django_filters import rest_framework as filters
from django.db.models import Q
from .models import BlogPost, Category, Tag

class BlogPostFilter(filters.FilterSet):
    """
    Advanced filtering for blog posts
    """
    # Date filtering
    date_from = filters.DateFilter(field_name='publication_date', lookup_expr='gte')
    date_to = filters.DateFilter(field_name='publication_date', lookup_expr='lte')
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    # Text search
    search = filters.CharFilter(method='filter_search')
    
    # Category and tags
    category = filters.ModelChoiceFilter(queryset=Category.objects.all())
    category_name = filters.CharFilter(field_name='category__name', lookup_expr='icontains')
    tags = filters.ModelMultipleChoiceFilter(queryset=Tag.objects.all())
    tag_names = filters.CharFilter(method='filter_by_tag_names')
    
    # Author filtering
    author = filters.CharFilter(field_name='author__username', lookup_expr='icontains')
    author_id = filters.NumberFilter(field_name='author__id')
    
    # Status and visibility
    status = filters.ChoiceFilter(choices=BlogPost.STATUS_CHOICES)
    is_public = filters.BooleanFilter()
    
    # Engagement metrics
    min_views = filters.NumberFilter(field_name='view_count', lookup_expr='gte')
    max_views = filters.NumberFilter(field_name='view_count', lookup_expr='lte')
    
    class Meta:
        model = BlogPost
        fields = [
            'date_from', 'date_to', 'created_after', 'created_before',
            'search', 'category', 'category_name', 'tags', 'tag_names',
            'author', 'author_id', 'status', 'is_public',
            'min_views', 'max_views'
        ]
    
    def filter_search(self, queryset, name, value):
        """
        Search across title, content, and excerpt
        """
        return queryset.filter(
            Q(title__icontains=value) |
            Q(content__icontains=value) |
            Q(excerpt__icontains=value)
        )
    
    def filter_by_tag_names(self, queryset, name, value):
        """
        Filter by tag names (comma-separated)
        """
        tag_names = [tag.strip() for tag in value.split(',')]
        return queryset.filter(tags__name__in=tag_names).distinct()