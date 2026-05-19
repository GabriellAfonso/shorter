"""Tests for guest-specific restrictions in create_short_url."""

from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.accounts.tests.factories import GuestUserFactory
from apps.links.services.link_service import create_short_url
from apps.links.tests.factories import ShortURLFactory
from core.exceptions import QuotaExceeded

pytestmark = pytest.mark.unit


@pytest.mark.django_db
class TestGuestRestrictions:
    def test_guest_link_gets_forced_ttl(self, settings):
        settings.GUEST_LINK_TTL_HOURS = 24
        guest = GuestUserFactory()

        link = create_short_url(original_url="https://example.com", owner=guest)

        assert link.expires_at is not None
        delta = link.expires_at - timezone.now()
        assert timedelta(hours=23, minutes=59) <= delta <= timedelta(hours=24, minutes=1)

    def test_guest_ttl_overrides_user_supplied_expiry(self, settings):
        settings.GUEST_LINK_TTL_HOURS = 24
        guest = GuestUserFactory()
        far_future = timezone.now() + timedelta(days=365)

        link = create_short_url(
            original_url="https://example.com",
            owner=guest,
            expires_at=far_future,
        )

        assert link.expires_at < far_future

    def test_guest_cannot_use_custom_slug(self):
        guest = GuestUserFactory()
        with pytest.raises(ValidationError):
            create_short_url(
                original_url="https://example.com",
                owner=guest,
                custom_slug="mycoolslug",
            )

    def test_guest_quota_enforced(self, settings):
        settings.GUEST_MAX_LINKS = 2
        guest = GuestUserFactory()

        create_short_url(original_url="https://a.com", owner=guest)
        create_short_url(original_url="https://b.com", owner=guest)

        with pytest.raises(QuotaExceeded):
            create_short_url(original_url="https://c.com", owner=guest)

    def test_normal_user_uses_higher_quota(self, settings):
        settings.GUEST_MAX_LINKS = 2
        settings.MAX_LINKS_PER_USER = 5
        from apps.accounts.tests.factories import UserFactory

        user = UserFactory()
        for i in range(3):
            ShortURLFactory(owner=user)

        link = create_short_url(original_url="https://example.com", owner=user)
        assert link.pk is not None
        assert link.expires_at is None
