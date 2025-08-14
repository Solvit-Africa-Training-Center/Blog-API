# ===== downloads/utils.py =====
import csv
import json
import xml.etree.ElementTree as ET
from io import StringIO, BytesIO
from django.http import HttpResponse
from django.utils import timezone
from django.core.serializers import serialize
import time
import logging

logger = logging.getLogger(__name__)

class DataExporter:
    """
    Utility class for exporting data in different formats
    """
    
    @staticmethod
    def export_posts_to_json(queryset):
        """
        Export blog posts to JSON format
        """
        posts_data = []
        
        for post in queryset:
            post_data = {
                'id': post.id,
                'title': post.title,
                'content': post.content,
                'excerpt': post.excerpt,
                'author': {
                    'username': post.author.username,
                    'email': post.author.email,
                    'full_name': post.author.get_full_name(),
                },
                'category': {
                    'name': post.category.name if post.category else None,
                    'slug': post.category.slug if post.category else None,
                },
                'tags': [{'name': tag.name, 'slug': tag.slug} for tag in post.tags.all()],
                'is_public': post.is_public,
                'status': post.status,
                'view_count': post.view_count,
                'like_count': post.like_count,
                'created_at': post.created_at.isoformat(),
                'updated_at': post.updated_at.isoformat(),
                'publication_date': post.publication_date.isoformat() if post.publication_date else None,
            }
            posts_data.append(post_data)
        
        return json.dumps({
            'export_date': timezone.now().isoformat(),
            'total_posts': len(posts_data),
            'posts': posts_data
        }, indent=2)
    
    @staticmethod
    def export_posts_to_csv(queryset):
        """
        Export blog posts to CSV format
        """
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        header = [
            'ID', 'Title', 'Content', 'Excerpt', 'Author Username', 'Author Email',
            'Category', 'Tags', 'Is Public', 'Status', 'View Count', 'Like Count',
            'Created At', 'Updated At', 'Publication Date'
        ]
        writer.writerow(header)
        
        # Write data
        for post in queryset:
            tags = ', '.join([tag.name for tag in post.tags.all()])
            row = [
                post.id,
                post.title,
                post.content,
                post.excerpt,
                post.author.username,
                post.author.email,
                post.category.name if post.category else '',
                tags,
                post.is_public,
                post.status,
                post.view_count,
                post.like_count,
                post.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                post.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                post.publication_date.strftime('%Y-%m-%d %H:%M:%S') if post.publication_date else '',
            ]
            writer.writerow(row)
        
        return output.getvalue()
    
    @staticmethod
    def export_posts_to_xml(queryset):
        """
        Export blog posts to XML format
        """
        root = ET.Element('blog_export')
        root.set('export_date', timezone.now().isoformat())
        root.set('total_posts', str(queryset.count()))
        
        posts_element = ET.SubElement(root, 'posts')
        
        for post in queryset:
            post_element = ET.SubElement(posts_element, 'post')
            post_element.set('id', str(post.id))
            
            # Basic fields
            ET.SubElement(post_element, 'title').text = post.title
            ET.SubElement(post_element, 'content').text = post.content
            ET.SubElement(post_element, 'excerpt').text = post.excerpt or ''
            ET.SubElement(post_element, 'is_public').text = str(post.is_public)
            ET.SubElement(post_element, 'status').text = post.status
            ET.SubElement(post_element, 'view_count').text = str(post.view_count)
            ET.SubElement(post_element, 'like_count').text = str(post.like_count)
            ET.SubElement(post_element, 'created_at').text = post.created_at.isoformat()
            ET.SubElement(post_element, 'updated_at').text = post.updated_at.isoformat()
            
            if post.publication_date:
                ET.SubElement(post_element, 'publication_date').text = post.publication_date.isoformat()
            
            # Author
            author_element = ET.SubElement(post_element, 'author')
            ET.SubElement(author_element, 'username').text = post.author.username
            ET.SubElement(author_element, 'email').text = post.author.email
            ET.SubElement(author_element, 'full_name').text = post.author.get_full_name()
            
            # Category
            if post.category:
                category_element = ET.SubElement(post_element, 'category')
                ET.SubElement(category_element, 'name').text = post.category.name
                ET.SubElement(category_element, 'slug').text = post.category.slug
            
            # Tags
            tags_element = ET.SubElement(post_element, 'tags')
            for tag in post.tags.all():
                tag_element = ET.SubElement(tags_element, 'tag')
                ET.SubElement(tag_element, 'name').text = tag.name
                ET.SubElement(tag_element, 'slug').text = tag.slug
        
        return ET.tostring(root, encoding='unicode')

def get_client_ip(request):
    """
    Get client IP address from request
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def create_download_response(content, filename, content_type):
    """
    Create HTTP response for file download
    """
    response = HttpResponse(content, content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response['Content-Length'] = len(content.encode('utf-8'))