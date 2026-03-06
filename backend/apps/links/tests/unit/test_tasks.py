"""
Tests for Celery tasks in the links feature.
Covers: deactivate_expired_links cache invalidation, return value, and periodic schedule.
"""
import pytest

pytestmark = pytest.mark.unit
from django.core.cache import cache
from django.utils import timezone

from apps.links.tasks import deactivate_expired_links
from apps.links.tests.factories import ExpiredShortURLFactory, ShortURLFactory


@pytest.mark.django_db
class TestDeactivateExpiredLinks:

    def test_returns_count_of_deactivated_links(self):
        ExpiredShortURLFactory.create_batch(3)
        result = deactivate_expired_links()
        assert result == 3

    def test_expired_links_set_inactive(self):
        link = ExpiredShortURLFactory()
        deactivate_expired_links()
        link.refresh_from_db()
        assert link.is_active is False

    def test_expired_links_cache_keys_deleted(self):
        link = ExpiredShortURLFactory()
        cache.set(f"redirect:{link.slug}", link.original_url)
        assert cache.get(f"redirect:{link.slug}") is not None

        deactivate_expired_links()

        assert cache.get(f"redirect:{link.slug}") is None

    def test_non_expired_links_not_affected(self):
        active = ShortURLFactory(expires_at=None)
        future = ShortURLFactory(
            expires_at=timezone.now() + timezone.timedelta(hours=1)
        )
        cache.set(f"redirect:{active.slug}", active.original_url)
        cache.set(f"redirect:{future.slug}", future.original_url)

        result = deactivate_expired_links()

        assert result == 0
        active.refresh_from_db()
        future.refresh_from_db()
        assert active.is_active is True
        assert future.is_active is True
        assert cache.get(f"redirect:{active.slug}") == active.original_url
        assert cache.get(f"redirect:{future.slug}") == future.original_url

    def test_links_with_no_expiry_not_deactivated(self):
        link = ShortURLFactory(expires_at=None)
        result = deactivate_expired_links()
        assert result == 0
        link.refresh_from_db()
        assert link.is_active is True

    def test_returns_zero_when_no_expired_links(self):
        ShortURLFactory.create_batch(2)
        result = deactivate_expired_links()
        assert result == 0


@pytest.mark.django_db
class TestDeactivateExpiredLinksPeriodicSchedule:
    """The migration must register the task in django-celery-beat correctly."""

    def test_periodic_task_exists(self):
        from django_celery_beat.models import PeriodicTask
        assert PeriodicTask.objects.filter(name="Deactivate expired links").exists()

    def test_periodic_task_points_to_correct_task(self):
        from django_celery_beat.models import PeriodicTask
        pt = PeriodicTask.objects.get(name="Deactivate expired links")
        assert pt.task == "apps.links.tasks.deactivate_expired_links"

    def test_periodic_task_interval_is_10_minutes(self):
        from django_celery_beat.models import PeriodicTask
        pt = PeriodicTask.objects.get(name="Deactivate expired links")
        assert pt.interval.every == 10
        assert pt.interval.period == "minutes"

    def test_running_migration_twice_does_not_duplicate(self):
        import importlib
        from django.apps import apps as django_apps
        from django_celery_beat.models import IntervalSchedule, PeriodicTask

        migration = importlib.import_module(
            "apps.links.migrations.0002_periodic_task_deactivate_expired_links"
        )
        create_periodic_task = migration.create_periodic_task

        # Simulate running the migration a second time; get_or_create must prevent duplicates
        create_periodic_task(django_apps, None)
        create_periodic_task(django_apps, None)

        assert PeriodicTask.objects.filter(name="Deactivate expired links").count() == 1
        assert IntervalSchedule.objects.filter(every=10, period="minutes").count() == 1
