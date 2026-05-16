"""
Management command: create_test_slugs
Creates 100 short URLs (test0000–test0099) for load testing.

Usage:
    python manage.py create_test_slugs
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.links.models.short_url import ShortURL

User = get_user_model()

TARGET_URL = "https://example.com"
SLUG_PREFIX = "test"
SLUG_COUNT = 100


class Command(BaseCommand):
    help = "Create 100 test slugs (test0000–test0099) for load testing."

    def handle(self, *args, **options) -> None:
        owner = User.objects.order_by("date_joined").first()
        if owner is None:
            raise CommandError("No users found. Create at least one user first.")

        created_count = 0
        for i in range(SLUG_COUNT):
            slug = f"{SLUG_PREFIX}{i:04d}"
            _, created = ShortURL.objects.get_or_create(
                slug=slug,
                defaults={
                    "original_url": TARGET_URL,
                    "title": f"Load test slug {slug}",
                    "owner": owner,
                },
            )
            if created:
                created_count += 1

        skipped = SLUG_COUNT - created_count
        self.stdout.write(
            self.style.SUCCESS(f"Done. Created: {created_count}, already existed: {skipped}.")
        )
