"""
Tests for links API views.
Covers: CRUD, analytics, redirect endpoint, ownership enforcement.
"""
import pytest

pytestmark = pytest.mark.integration
from rest_framework import status

from apps.links.tests.factories import ExpiredShortURLFactory, ShortURLFactory
from apps.accounts.tests.factories import UserFactory

LINKS_URL = "/api/v1/links/"


@pytest.mark.django_db
class TestLinkListCreate:
    def test_list_returns_only_own_links(self, auth_client):
        ShortURLFactory.create_batch(3, owner=auth_client._user)
        ShortURLFactory.create_batch(2, owner=UserFactory())  # another user

        response = auth_client.get(LINKS_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["pagination"]["count"] == 3

    def test_list_excludes_deleted_links(self, auth_client):
        ShortURLFactory.create_batch(2, owner=auth_client._user, is_active=True)
        ShortURLFactory(owner=auth_client._user, is_active=False)  # soft-deleted

        response = auth_client.get(LINKS_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["pagination"]["count"] == 2

    def test_create_link_auto_slug(self, auth_client):
        payload = {"original_url": "https://example.com"}
        response = auth_client.post(LINKS_URL, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert len(data["slug"]) == 8
        assert data["original_url"] == "https://example.com"

    def test_create_link_custom_slug(self, auth_client):
        payload = {"original_url": "https://example.com", "slug": "mylink"}
        response = auth_client.post(LINKS_URL, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["slug"] == "mylink"

    def test_create_link_duplicate_slug_returns_400(self, auth_client):
        ShortURLFactory(slug="taken")
        payload = {"original_url": "https://example.com", "slug": "taken"}
        response = auth_client.post(LINKS_URL, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_link_invalid_url_returns_400(self, auth_client):
        payload = {"original_url": "not-a-url"}
        response = auth_client.post(LINKS_URL, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_includes_stats(self, auth_client):
        ShortURLFactory.create_batch(2, owner=auth_client._user, click_count=5)
        ShortURLFactory(owner=auth_client._user, click_count=3, is_active=False)

        response = auth_client.get(LINKS_URL)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "stats" in data
        assert data["stats"]["total_clicks"] == 13  # 5 + 5 + 3 (includes inactive)
        assert data["stats"]["active_count"] == 2

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get(LINKS_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestLinkDetail:
    def test_get_own_link(self, auth_client):
        link = ShortURLFactory(owner=auth_client._user)
        response = auth_client.get(f"{LINKS_URL}{link.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["slug"] == link.slug

    def test_get_other_user_link_returns_404(self, auth_client):
        other_link = ShortURLFactory(owner=UserFactory())
        response = auth_client.get(f"{LINKS_URL}{other_link.id}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_own_link(self, auth_client):
        link = ShortURLFactory(owner=auth_client._user)
        response = auth_client.delete(f"{LINKS_URL}{link.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Re-check the link is soft-deleted.
        from apps.links.models import ShortURL
        link.refresh_from_db()
        assert link.is_active is False

    def test_delete_other_user_link_returns_404(self, auth_client):
        other_link = ShortURLFactory(owner=UserFactory())
        response = auth_client.delete(f"{LINKS_URL}{other_link.id}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestRedirectEndpoint:
    def test_valid_slug_redirects(self, client):
        link = ShortURLFactory(original_url="https://target.example.com")
        response = client.get(f"/s/{link.slug}/", follow=False)
        assert response.status_code == 302
        assert response["Location"] == "https://target.example.com"

    def test_invalid_slug_returns_404(self, client):
        response = client.get("/s/nonexistentslug/", follow=False)
        assert response.status_code == 404

    def test_expired_link_returns_404(self, client):
        link = ExpiredShortURLFactory()
        response = client.get(f"/s/{link.slug}/", follow=False)
        assert response.status_code == 404

    def test_inactive_link_returns_404(self, client):
        link = ShortURLFactory(is_active=False)
        response = client.get(f"/s/{link.slug}/", follow=False)
        assert response.status_code == 404

    def test_rate_limited_returns_429_with_retry_after(self, client):
        from unittest.mock import patch
        from django.test import override_settings

        link = ShortURLFactory()
        with override_settings(REDIRECT_RATE_LIMIT=1):
            with patch("apps.links.redirect_views._is_rate_limited", return_value=True):
                response = client.get(f"/s/{link.slug}/", follow=False)

        assert response.status_code == 429
        assert "Retry-After" in response


@pytest.mark.django_db
class TestLinkAnalytics:
    def test_analytics_returns_expected_shape(self, auth_client):
        from apps.links.tests.factories import LinkClickFactory
        link = ShortURLFactory(owner=auth_client._user, click_count=5)
        LinkClickFactory.create_batch(5, link=link)

        response = auth_client.get(f"{LINKS_URL}{link.id}/analytics/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_clicks" in data
        assert "daily_clicks" in data
        assert "by_device" in data
        assert "top_referrers" in data

    def test_analytics_other_user_returns_404(self, auth_client):
        other_link = ShortURLFactory(owner=UserFactory())
        response = auth_client.get(f"{LINKS_URL}{other_link.id}/analytics/")
        assert response.status_code == status.HTTP_404_NOT_FOUND
