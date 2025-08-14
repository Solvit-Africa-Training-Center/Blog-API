from django.core.management.base import BaseCommand
from django.utils import timezone
from downloads.models import DownloadLog
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    """
    Management command to clean up old download logs
    """
    help = 'Clean up download logs older than specified days'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Delete logs older than this many days (default: 90)'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )
    
    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        
        old_logs = DownloadLog.objects.filter(requested_at__lt=cutoff_date)
        count = old_logs.count()
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: Would delete {count} download logs older than {days} days')
            )
        else:
            deleted_count, _ = old_logs.delete()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully deleted {deleted_count} download logs older than {days} days')
            )
            logger.info(f'Cleaned up {deleted_count} old download logs')