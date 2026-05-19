"""Integration tests for the guest login endpoint and lifecycle."""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.services.user_service import GUEST_EMAIL_DOMAIN, GUEST_EMAIL_PREFIX
from apps.accounts.tasks import purge_guest_accounts
from apps.accounts.tests.factories import GuestUserFactory, UserFactory

pytestmark = pytest.mark.integration

GUEST_URL = "/api/v1/auth/guest/"
REGISTER_URL = "/api/v1/auth/register/"

User = get_user_model()


@pytest.mark.django_db
class TestGuestLogin:
    def test_creates_new_guest_account(self, api_client):
        response = api_client.post(GUEST_URL, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        assert data["user"]["is_guest"] is True
        assert data["user"]["email"].startswith(GUEST_EMAIL_PREFIX)
        assert data["user"]["email"].endswith(f"@{GUEST_EMAIL_DOMAIN}")
        assert "access" in data["tokens"]
        assert "refresh" in data["tokens"]

        assert User.objects.filter(email=data["user"]["email"], is_guest=True).exists()

    def test_reuses_existing_guest_when_token_provided(self, api_client):
        guest = GuestUserFactory()
        access = str(RefreshToken.for_user(guest).access_token)

        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = api_client.post(GUEST_URL, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["user"]["id"] == guest.pk
        assert User.objects.filter(is_guest=True).count() == 1

    def test_invalid_token_creates_new_guest(self, api_client):
        api_client.credentials(HTTP_AUTHORIZATION="Bearer not-a-token")
        response = api_client.post(GUEST_URL, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    def test_non_guest_token_creates_new_guest(self, api_client):
        normal = UserFactory()
        access = str(RefreshToken.for_user(normal).access_token)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        response = api_client.post(GUEST_URL, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["user"]["is_guest"] is True
        assert response.json()["user"]["id"] != normal.pk


@pytest.mark.django_db
class TestRegisterBlocksGuestEmails:
    def test_register_rejects_guest_email_domain(self, api_client):
        payload = {
            "email": f"someone@{GUEST_EMAIL_DOMAIN}",
            "password": "securepass1",
        }
        response = api_client.post(REGISTER_URL, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_rejects_guest_email_prefix(self, api_client):
        payload = {
            "email": f"{GUEST_EMAIL_PREFIX}abc@example.com",
            "password": "securepass1",
        }
        response = api_client.post(REGISTER_URL, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestPurgeGuestAccounts:
    def test_deletes_only_old_guests(self, settings):
        settings.GUEST_ACCOUNT_PURGE_HOURS = 48

        old_guest = GuestUserFactory()
        User.objects.filter(pk=old_guest.pk).update(created_at=timezone.now() - timedelta(hours=72))

        recent_guest = GuestUserFactory()
        normal_user = UserFactory()
        User.objects.filter(pk=normal_user.pk).update(
            created_at=timezone.now() - timedelta(hours=72)
        )

        purge_guest_accounts()

        assert not User.objects.filter(pk=old_guest.pk).exists()
        assert User.objects.filter(pk=recent_guest.pk).exists()
        assert User.objects.filter(pk=normal_user.pk).exists()
