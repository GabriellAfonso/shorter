"""Unit tests for link_selector.get_link_by_slug edge cases."""

import pytest

from apps.links.selectors.link_selector import get_link_by_slug
from apps.links.tests.factories import ExpiredShortURLFactory, ShortURLFactory
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
