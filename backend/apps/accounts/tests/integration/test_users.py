"""
Tests for the users feature.
Covers: profile retrieval, profile update, password change.
"""
import pytest

pytestmark = pytest.mark.integration
from rest_framework import status


@pytest.mark.django_db
class TestMeEndpoint:
    url = "/api/v1/users/me/"

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_authenticated_returns_profile(self, auth_client):
        response = auth_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == auth_client._user.email
        assert "links_count" in data

    def test_response_does_not_expose_password(self, auth_client):
        response = auth_client.get(self.url)
        assert "password" not in response.json()


@pytest.mark.django_db
class TestUpdateProfile:
    url = "/api/v1/users/me/update/"

    def test_patch_updates_fields(self, auth_client):
        payload = {"first_name": "Alice", "bio": "Hello world"}
        response = auth_client.patch(self.url, payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["first_name"] == "Alice"
        assert data["bio"] == "Hello world"

    def test_patch_with_empty_body_is_noop(self, auth_client):
        response = auth_client.patch(self.url, {}, format="json")
        assert response.status_code == status.HTTP_200_OK

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.patch(self.url, {"first_name": "X"}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestChangePassword:
    url = "/api/v1/users/me/change-password/"

    def test_change_password_success(self, auth_client):
        payload = {
            "old_password": "testpass123",
            "new_password": "newstrongpass!",
            "confirm_password": "newstrongpass!",
        }
        response = auth_client.post(self.url, payload, format="json")
        assert response.status_code == status.HTTP_200_OK

    def test_wrong_old_password_returns_400(self, auth_client):
        payload = {
            "old_password": "wrongpassword",
            "new_password": "newstrongpass!",
            "confirm_password": "newstrongpass!",
        }
        response = auth_client.post(self.url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_mismatched_passwords_returns_400(self, auth_client):
        payload = {
            "old_password": "testpass123",
            "new_password": "passA",
            "confirm_password": "passB",
        }
        response = auth_client.post(self.url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestChangePasswordTokenInvalidation:
    """change_password must blacklist all outstanding tokens for the user."""

    CHANGE_URL = "/api/v1/users/me/change-password/"
    REFRESH_URL = "/api/v1/auth/token/refresh/"
    PAYLOAD = {
        "old_password": "testpass123",
        "new_password": "newstrongpass!",
        "confirm_password": "newstrongpass!",
    }

    def test_all_outstanding_tokens_blacklisted(self, auth_client):
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

        user = auth_client._user
        # Issue a couple of extra tokens to ensure all are invalidated, not just the last one
        RefreshToken.for_user(user)
        RefreshToken.for_user(user)

        outstanding_ids = set(OutstandingToken.objects.filter(user=user).values_list("id", flat=True))
        assert outstanding_ids, "pre-condition: tokens must exist before change"

        auth_client.post(self.CHANGE_URL, self.PAYLOAD, format="json")

        blacklisted_token_ids = set(
            BlacklistedToken.objects.filter(token__user=user).values_list("token_id", flat=True)
        )
        assert outstanding_ids.issubset(blacklisted_token_ids)

    def test_refresh_token_rejected_after_password_change(self, auth_client, api_client):
        from rest_framework_simplejwt.tokens import RefreshToken

        user = auth_client._user
        refresh = RefreshToken.for_user(user)

        auth_client.post(self.CHANGE_URL, self.PAYLOAD, format="json")

        response = api_client.post(self.REFRESH_URL, {"refresh": str(refresh)}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_other_user_tokens_not_blacklisted(self, auth_client):
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
        from apps.accounts.tests.factories import UserFactory

        other_user = UserFactory()
        other_refresh = RefreshToken.for_user(other_user)
        other_token_obj = OutstandingToken.objects.get(jti=other_refresh["jti"])

        auth_client.post(self.CHANGE_URL, self.PAYLOAD, format="json")

        assert not BlacklistedToken.objects.filter(token=other_token_obj).exists()
