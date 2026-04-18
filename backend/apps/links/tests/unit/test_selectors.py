"""Unit tests for link selectors."""

from datetime import timedelta

import pytest
from django.core.cache import cache
from django.utils import timezone

from apps.accounts.tests.factories import UserFactory
from apps.links.models.link_click import LinkClick
from apps.links.selectors.link_selector import (
    get_cached_link_analytics,
    get_link_analytics,
    get_link_by_slug,
    get_user_link_stats,
    invalidate_analytics_cache,
    slug_exists,
)
from apps.links.tests.factories import ExpiredShortURLFactory, LinkClickFactory, ShortURLFactory
from core.exceptions import NotFound

pytestmark = pytest.mark.unit


@pytest.mark.django_db
class TestGetLinkBySlug:
    def test_returns_link_for_valid_active_slug(self):
        link = ShortURLFactory(is_active=True)
        result = get_link_by_slug(link.slug)
        assert result.id == link.id

    def test_raises_not_found_for_inactive_link(self):
        link = ShortURLFactory(is_active=False)
        with pytest.raises(NotFound):
            get_link_by_slug(link.slug)

    def test_raises_not_found_for_expired_link(self):
        link = ExpiredShortURLFactory()
        with pytest.raises(NotFound):
            get_link_by_slug(link.slug)

    def test_raises_not_found_for_nonexistent_slug(self):
        with pytest.raises(NotFound):
            get_link_by_slug("doesnotexist")


@pytest.mark.django_db
class TestSlugExists:
    def test_returns_true_for_existing_slug(self):
        link = ShortURLFactory(slug="existing")
        assert slug_exists(link.slug) is True

    def test_returns_false_for_nonexistent_slug(self):
        assert slug_exists("nope") is False

    def test_includes_inactive_links(self):
        link = ShortURLFactory(slug="inactive", is_active=False)
        assert slug_exists(link.slug) is True


@pytest.mark.django_db
class TestGetUserLinkStats:
    def test_no_links_returns_zeros(self):
        user = UserFactory()
        stats = get_user_link_stats(user)
        assert stats["total_clicks"] == 0
        assert stats["active_count"] == 0

    def test_total_clicks_sums_all_links_including_inactive(self):
        user = UserFactory()
        ShortURLFactory(owner=user, click_count=10, is_active=True)
        ShortURLFactory(owner=user, click_count=5, is_active=False)
        stats = get_user_link_stats(user)
        assert stats["total_clicks"] == 15

    def test_active_count_excludes_inactive_links(self):
        user = UserFactory()
        ShortURLFactory.create_batch(3, owner=user, is_active=True)
        ShortURLFactory(owner=user, is_active=False)
        stats = get_user_link_stats(user)
        assert stats["active_count"] == 3

    def test_active_count_excludes_expired_links(self):
        user = UserFactory()
        ShortURLFactory(owner=user, is_active=True)
        ExpiredShortURLFactory(owner=user, is_active=True)
        stats = get_user_link_stats(user)
        assert stats["active_count"] == 1

    def test_does_not_include_other_users_stats(self):
        user = UserFactory()
        other = UserFactory()
        ShortURLFactory(owner=other, click_count=100, is_active=True)
        stats = get_user_link_stats(user)
        assert stats["total_clicks"] == 0
        assert stats["active_count"] == 0


@pytest.mark.django_db
class TestGetLinkAnalytics:
    def test_total_clicks_reflects_click_count_field(self):
        link = ShortURLFactory(click_count=42)
        result = get_link_analytics(link)
        assert result["total_clicks"] == 42

    def test_period_days_in_result(self):
        link = ShortURLFactory()
        assert get_link_analytics(link, days=7)["period_days"] == 7

    def test_clicks_in_period_counts_recent_clicks(self):
        link = ShortURLFactory()
        LinkClickFactory.create_batch(3, link=link)
        assert get_link_analytics(link, days=30)["clicks_in_period"] == 3

    def test_excludes_clicks_outside_period(self):
        link = ShortURLFactory()
        old = LinkClickFactory(link=link)
        LinkClick.objects.filter(pk=old.pk).update(timestamp=timezone.now() - timedelta(days=60))
        LinkClickFactory(link=link)  # recent
        assert get_link_analytics(link, days=30)["clicks_in_period"] == 1

    def test_by_device_breakdown_counts_correctly(self):
        link = ShortURLFactory()
        LinkClickFactory.create_batch(3, link=link, device_type="mobile")
        LinkClickFactory(link=link, device_type="desktop")
        by_device = {d["device_type"]: d["count"] for d in get_link_analytics(link)["by_device"]}
        assert by_device["mobile"] == 3
        assert by_device["desktop"] == 1

    def test_top_referrers_excludes_empty_strings(self):
        link = ShortURLFactory()
        LinkClickFactory.create_batch(2, link=link, referrer="https://google.com")
        LinkClickFactory(link=link, referrer="")
        referrers = [r["referrer"] for r in get_link_analytics(link)["top_referrers"]]
        assert "" not in referrers


@pytest.mark.django_db
class TestGetCachedLinkAnalytics:
    def test_cache_miss_fetches_from_db(self):
        link = ShortURLFactory(click_count=5)
        result = get_cached_link_analytics(link, days=30)
        assert result["total_clicks"] == 5

    def test_cache_hit_returns_cached_result(self):
        link = ShortURLFactory(click_count=5)
        get_cached_link_analytics(link, days=30)  # populate cache
        # Mutate DB — cache should shield the old value
        from apps.links.models.short_url import ShortURL

        ShortURL.objects.filter(pk=link.pk).update(click_count=999)
        result = get_cached_link_analytics(link, days=30)
        assert result["total_clicks"] == 5

    def test_different_day_ranges_cached_independently(self):
        link = ShortURLFactory()
        get_cached_link_analytics(link, days=7)
        get_cached_link_analytics(link, days=30)
        assert cache.get(f"analytics:{link.id}:7") is not None
        assert cache.get(f"analytics:{link.id}:30") is not None


@pytest.mark.django_db
class TestInvalidateAnalyticsCache:
    def test_clears_all_four_day_variants(self):
        link = ShortURLFactory()
        for days in (7, 30, 90, 365):
            cache.set(f"analytics:{link.id}:{days}", {"dummy": True}, 60)

        invalidate_analytics_cache(str(link.id))

        for days in (7, 30, 90, 365):
            assert cache.get(f"analytics:{link.id}:{days}") is None
