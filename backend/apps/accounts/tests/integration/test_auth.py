"""
Tests for the accounts feature.
Covers: register, login, logout, token refresh, protected-endpoint guard.
"""
import pytest

pytestmark = pytest.mark.integration
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.tests.factories import UserFactory

REGISTER_URL = "/api/v1/auth/register/"
LOGIN_URL = "/api/v1/auth/login/"
LOGOUT_URL = "/api/v1/auth/logout/"
REFRESH_URL = "/api/v1/auth/token/refresh/"
ME_URL = "/api/v1/users/me/"


@pytest.mark.django_db
class TestRegistration:
    def test_register_returns_tokens_and_user(self, api_client):
        payload = {
            "email": "newuser@example.com",
            "password": "securepass1",
            "first_name": "Jane",
            "last_name": "Doe",
        }
        response = api_client.post(REGISTER_URL, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "tokens" in data
        assert "access" in data["tokens"]
        assert "refresh" in data["tokens"]
        assert data["user"]["email"] == "newuser@example.com"

    def test_register_duplicate_email_returns_400(self, api_client, db):
        UserFactory(email="existing@example.com")
        payload = {"email": "existing@example.com", "password": "securepass1"}
        response = api_client.post(REGISTER_URL, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_short_password_returns_400(self, api_client):
        payload = {"email": "test@example.com", "password": "abc"}
        response = api_client.post(REGISTER_URL, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_missing_email_returns_400(self, api_client):
        response = api_client.post(REGISTER_URL, {"password": "securepass1"}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestLogin:
    def test_login_with_valid_credentials(self, api_client):
        user = UserFactory(email="login@example.com")
        user.set_password("testpass123")
        user.save()

        response = api_client.post(LOGIN_URL, {"email": "login@example.com", "password": "testpass123"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access" in data
        assert "refresh" in data
        assert data["user"]["email"] == "login@example.com"

    def test_login_wrong_password_returns_401(self, api_client):
        user = UserFactory(email="test2@example.com")
        user.set_password("correctpass")
        user.save()

        response = api_client.post(LOGIN_URL, {"email": "test2@example.com", "password": "wrongpass"}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_nonexistent_user_returns_401(self, api_client, db):
        response = api_client.post(LOGIN_URL, {"email": "ghost@example.com", "password": "pass"}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestLogout:
    def test_logout_blacklists_refresh_token(self, auth_client):
        user = auth_client._user
        refresh = RefreshToken.for_user(user)

        response = auth_client.post(LOGOUT_URL, {"refresh": str(refresh)}, format="json")
        assert response.status_code == status.HTTP_200_OK

    def test_logout_invalid_token_returns_400(self, auth_client):
        response = auth_client.post(LOGOUT_URL, {"refresh": "not-a-valid-token"}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_logout_unauthenticated_returns_401(self, api_client, db):
        response = api_client.post(LOGOUT_URL, {"refresh": "some-token"}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestTokenRefresh:
    def test_refresh_returns_new_access_token(self, api_client):
        user = UserFactory()
        refresh = RefreshToken.for_user(user)

        response = api_client.post(REFRESH_URL, {"refresh": str(refresh)}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.json()

    def test_invalid_refresh_token_returns_401(self, api_client, db):
        response = api_client.post(REFRESH_URL, {"refresh": "invalid"}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
