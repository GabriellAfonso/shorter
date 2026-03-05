"""
Tests for links domain models.
Covers: ShortURL properties, LinkClick creation, expiry logic.
"""
import pytest
from django.utils import timezone

from apps.links.tests.factories import ExpiredShortURLFactory, LinkClickFactory, ShortURLFactory


@pytest.mark.django_db
class TestShortURLModel:
    def test_str_contains_slug(self):
        link = ShortURLFactory(slug="abc123")
        assert "abc123" in str(link)

    def test_is_expired_false_for_future_expiry(self):
        future = timezone.now() + timezone.timedelta(days=1)
        link = ShortURLFactory(expires_at=future)
        assert link.is_expired is False

    def test_is_expired_true_for_past_expiry(self):
        link = ExpiredShortURLFactory()
        assert link.is_expired is True

    def test_is_expired_false_when_no_expiry(self):
        link = ShortURLFactory(expires_at=None)
        assert link.is_expired is False

    def test_short_url_contains_slug(self):
        link = ShortURLFactory(slug="myslug")
        assert "myslug" in link.short_url

    def test_click_count_default_is_zero(self):
        link = ShortURLFactory()
        assert link.click_count == 0


@pytest.mark.django_db
class TestLinkClickModel:
    def test_click_can_be_created(self):
        click = LinkClickFactory()
        assert click.pk is not None
        assert click.link is not None

    def test_str_contains_slug(self):
        click = LinkClickFactory()
        assert click.link.slug in str(click)
