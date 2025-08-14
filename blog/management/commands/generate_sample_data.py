# ===== blog/management/commands/generate_sample_data.py =====
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from blog.models import Category, Tag, BlogPost
from faker import Faker
import random

User = get_user_model()
fake = Faker()

class Command(BaseCommand):
    """
    Generate sample data for testing
    """
    help = 'Generate sample blog data for testing'
    
    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=5, help='Number of users to create')
        parser.add_argument('--posts', type=int, default=50, help='Number of posts to create')
        parser.add_argument('--categories', type=int, default=10, help='Number of categories to create')
        parser.add_argument('--tags', type=int, default=20, help='Number of tags to create')
    
    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create users
        users = []
        for i in range(options['users']):
            username = fake.user_name()
            while User.objects.filter(username=username).exists():
                username = fake.user_name()
            
            user = User.objects.create_user(
                username=username,
                email=fake.email(),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                bio=fake.text(max_nb_chars=200),
                password='testpass123'
            )
            users.append(user)
        
        self.stdout.write(f'Created {len(users)} users')
        
        # Create categories
        categories = []
        for i in range(options['categories']):
            category = Category.objects.create(
                name=fake.word().title(),
                description=fake.sentence()
            )
            categories.append(category)
        
        self.stdout.write(f'Created {len(categories)} categories')
        
        # Create tags
        tags = []
        for i in range(options['tags']):
            tag_name = fake.word()
            while Tag.objects.filter(name=tag_name).exists():
                tag_name = fake.word()
            
            tag = Tag.objects.create(name=tag_name)
            tags.append(tag)
        
        self.stdout.write(f'Created {len(tags)} tags')
        
        # Create posts
        posts = []
        for i in range(options['posts']):
            post = BlogPost.objects.create(
                title=fake.sentence(nb_words=6)[:-1],  # Remove period
                content=fake.text(max_nb_chars=2000),
                excerpt=fake.text(max_nb_chars=200),
                author=random.choice(users),
                category=random.choice(categories),
                is_public=random.choice([True, True, True, False]),  # 75% public
                status=random.choice(['published', 'published', 'draft']),  # 66% published
                view_count=random.randint(0, 1000),
                like_count=random.randint(0, 100)
            )
            
            # Add random tags
            post_tags = random.sample(tags, random.randint(1, 5))
            post.tags.set(post_tags)
            
            posts.append(post)
        
        self.stdout.write(f'Created {len(posts)} blog posts')
        self.stdout.write(self.style.SUCCESS('Sample data created successfully!'))