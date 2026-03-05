"""
Management command: seed_data
Creates demo users, short URLs, and click history for a realistic demo.

Usage:
    python manage.py seed_data
    python manage.py seed_data --reset   # delete all existing data first
"""
import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.links.models.link_click import LinkClick
from apps.links.models.short_url import ShortURL
from apps.links.services.link_service import record_click

User = get_user_model()

DEMO_URLS = [
    ("github", "https://github.com", "My GitHub Profile"),
    ("linkedin", "https://linkedin.com", "LinkedIn"),
    ("portfolio", "https://example.com/portfolio", "My Portfolio"),
    ("blog", "https://dev.to", "Dev.to Blog"),
    ("docs", "https://docs.djangoproject.com", "Django Docs"),
    ("react", "https://react.dev", "React Docs"),
    ("tailwind", "https://tailwindcss.com", "Tailwind CSS"),
    ("vite", "https://vitejs.dev", "Vite"),
]

REFERRERS = [
    "https://google.com",
    "https://twitter.com",
    "https://linkedin.com",
    "https://github.com",
    "",
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/121.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0) AppleWebKit/605.1.15 Mobile/15E148",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 Chrome/121.0 Mobile",
]


class Command(BaseCommand):
    help = "Seed the database with demo users and short URLs."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete all existing links and demo users before seeding.",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            self.stdout.write("Resetting demo data...")
            User.objects.filter(email__in=["admin@demo.com", "user@demo.com"]).delete()
            self.stdout.write(self.style.WARNING("Demo data cleared."))

        admin_user = self._get_or_create_user(
            email="admin@demo.com",
            password="admin1234",
            first_name="Admin",
            last_name="Demo",
            is_staff=True,
            is_superuser=True,
        )

        regular_user = self._get_or_create_user(
            email="user@demo.com",
            password="demo1234",
            first_name="Jane",
            last_name="Doe",
        )

        for slug, url, title in DEMO_URLS:
            link, created = ShortURL.objects.get_or_create(
                slug=slug,
                defaults={
                    "original_url": url,
                    "title": title,
                    "owner": regular_user,
                },
            )
            if created:
                self._generate_clicks(link, count=random.randint(20, 150))
                self.stdout.write(f"  Created: /{slug}")

        self.stdout.write(self.style.SUCCESS("\nDemo data seeded successfully!"))
        self.stdout.write("  Admin: admin@demo.com / admin1234")
        self.stdout.write("  User:  user@demo.com / demo1234")

    def _get_or_create_user(self, email: str, password: str, **kwargs):
        user, created = User.objects.get_or_create(
            email=email,
            defaults=kwargs,
        )
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(f"Created user: {email}")
        return user

    def _generate_clicks(self, link: ShortURL, count: int) -> None:
        clicks = []
        for i in range(count):
            # Spread clicks over the last 30 days.
            days_ago = random.randint(0, 30)
            ua = random.choice(USER_AGENTS)
            from apps.links.services.link_service import _parse_user_agent

            device = _parse_user_agent(ua)
            clicks.append(
                LinkClick(
                    link=link,
                    ip_address=f"hashed_ip_{random.randint(1, 100)}",
                    user_agent=ua,
                    referrer=random.choice(REFERRERS),
                    browser=device["browser"],
                    os=device["os"],
                    device_type=device["device_type"],
                )
            )

        LinkClick.objects.bulk_create(clicks)
        ShortURL.objects.filter(pk=link.pk).update(click_count=count)
