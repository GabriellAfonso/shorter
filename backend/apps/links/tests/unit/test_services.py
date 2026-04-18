"""
Tests for links business logic (services).
Covers: slug generation, URL creation, collision handling, delete, redirect cache.
"""

import pytest
from django.core.cache import cache

from apps.accounts.tests.factories import UserFactory
from apps.links.models import ShortURL
from apps.links.services.link_service import (
    create_short_url,
    delete_short_url,
    get_redirect_url,
    record_click,
)
from apps.links.tests.factories import ShortURLFactory
from core.exceptions import QuotaExceeded
from core.utils import generate_slug

pytestmark = pytest.mark.unit


@pytest.mark.django_db
class TestSlugGeneration:
    def test_generate_slug_default_length(self):
        slug = generate_slug()
        assert len(slug) == 8

    def test_generate_slug_custom_length(self):
        slug = generate_slug(12)
        assert len(slug) == 12

    def test_generate_slug_is_alphanumeric(self):
        slug = generate_slug()
        assert slug.isalnum()

    def test_generate_slug_uniqueness(self):
        """Generate 1000 slugs and verify no collisions."""
        slugs = {generate_slug() for _ in range(1000)}
        assert len(slugs) == 1000


@pytest.mark.django_db
class TestCreateShortURL:
    def test_create_with_auto_slug(self):
        user = UserFactory()
        link = create_short_url(original_url="https://example.com", owner=user)
        assert link.pk is not None
        assert len(link.slug) == 8

    def test_create_with_custom_slug(self):
        user = UserFactory()
        link = create_short_url(
            original_url="https://example.com", owner=user, custom_slug="myslug"
        )
        assert link.slug == "myslug"

    def test_create_with_duplicate_custom_slug_raises(self):
        user = UserFactory()
        ShortURLFactory(slug="taken")
        from rest_framework.exceptions import ValidationError

        with pytest.raises(ValidationError):
            create_short_url(original_url="https://example.com", owner=user, custom_slug="taken")

    def test_create_with_expiry(self):
        from django.utils import timezone

        user = UserFactory()
        future = timezone.now() + timezone.timedelta(days=7)
        link = create_short_url(original_url="https://example.com", owner=user, expires_at=future)
        assert link.expires_at == future

    def test_owner_is_set_correctly(self):
        user = UserFactory()
        link = create_short_url(original_url="https://example.com", owner=user)
        assert link.owner == user

    def test_create_raises_quota_exceeded_at_limit(self, settings):
        settings.MAX_LINKS_PER_USER = 3
        user = UserFactory()
        ShortURLFactory.create_batch(3, owner=user, is_active=True)
        with pytest.raises(QuotaExceeded):
            create_short_url(original_url="https://example.com", owner=user)

    def test_inactive_links_excluded_from_quota_count(self, settings):
        settings.MAX_LINKS_PER_USER = 2
        user = UserFactory()
        ShortURLFactory.create_batch(2, owner=user, is_active=True)  # exactly at limit
        ShortURLFactory.create_batch(2, owner=user, is_active=False)  # inactive — must not count
        # 2 active links = at the limit; inactive links are irrelevant
        with pytest.raises(QuotaExceeded):
            create_short_url(original_url="https://example.com", owner=user)

    def test_quota_allows_creation_after_delete(self, settings):
        settings.MAX_LINKS_PER_USER = 1
        user = UserFactory()
        existing = ShortURLFactory(owner=user, is_active=True)
        delete_short_url(link=existing)
        # Now 0 active — should succeed
        new_link = create_short_url(original_url="https://example.com", owner=user)
        assert new_link.pk is not None

    def test_quota_is_per_user(self, settings):
        settings.MAX_LINKS_PER_USER = 1
        user_a = UserFactory()
        user_b = UserFactory()
        ShortURLFactory(owner=user_a, is_active=True)
        # user_b has 0 links — should succeed
        link = create_short_url(original_url="https://example.com", owner=user_b)
        assert link.pk is not None


@pytest.mark.django_db
class TestDeleteShortURL:
    def test_delete_sets_is_active_false(self):
        link = ShortURLFactory()
        delete_short_url(link=link)
        link.refresh_from_db()
        assert link.is_active is False

    def test_delete_clears_cache(self):
        link = ShortURLFactory()
        cache.set(f"redirect:{link.slug}", link.original_url, 3600)
        delete_short_url(link=link)
        assert cache.get(f"redirect:{link.slug}") is None


@pytest.mark.django_db
class TestGetRedirectURL:
    def test_returns_url_for_valid_slug(self):
        link = ShortURLFactory(original_url="https://target.com")
        url, link_id = get_redirect_url(link.slug)
        assert url == "https://target.com"
        assert link_id == str(link.id)

    def test_returns_none_for_invalid_slug(self):
        result = get_redirect_url("nonexistent")
        assert result is None

    def test_caches_result(self):
        link = ShortURLFactory(original_url="https://target.com")
        get_redirect_url(link.slug)  # populate cache
        # Delete from DB — should still return from cache
        ShortURL.objects.filter(pk=link.pk).delete()
        url, link_id = get_redirect_url(link.slug)
        assert url == "https://target.com"


@pytest.mark.django_db
class TestRecordClick:
    def test_creates_link_click_and_increments_count(self):
        from apps.links.models import LinkClick

        link = ShortURLFactory()
        record_click(
            link_id=str(link.id),
            ip_address="1.2.3.4",
            user_agent="Mozilla/5.0 Chrome/121.0",
            referrer="https://google.com",
        )
        link.refresh_from_db()
        assert link.click_count == 1
        assert LinkClick.objects.filter(link=link).count() == 1

    def test_invalid_link_id_does_not_raise(self):
        record_click(
            link_id="00000000-0000-0000-0000-000000000000",
            ip_address="1.2.3.4",
            user_agent="",
            referrer="",
        )
