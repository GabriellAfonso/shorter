"""
Management command: delete_test_slugs
Removes all short URLs with slugs test0000–test0099.

Usage:
    python manage.py delete_test_slugs
"""

from django.core.management.base import BaseCommand

from apps.links.models.short_url import ShortURL

SLUG_PREFIX = "test"
SLUG_COUNT = 100


class Command(BaseCommand):
    help = "Delete all test slugs (test0000–test0099)."

    def handle(self, *args, **options) -> None:
        slugs = [f"{SLUG_PREFIX}{i:04d}" for i in range(SLUG_COUNT)]
        deleted, _ = ShortURL.objects.filter(slug__in=slugs).delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted} test slug(s)."))
