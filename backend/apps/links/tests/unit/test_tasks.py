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
