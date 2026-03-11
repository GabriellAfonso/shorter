"""
Root pytest configuration.
Shared fixtures available to all test modules.
"""
import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture(autouse=True)
def use_locmem_cache(settings):
    """
    Replace Redis with an in-process cache for all tests so the suite can run
    without a live Redis server.  Individual integration tests that explicitly
    need Redis can override this fixture.
    """
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def user(db):
    from apps.accounts.tests.factories import UserFactory
    return UserFactory()


@pytest.fixture
def auth_client(api_client, user):
    """Authenticated API client."""
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    api_client._user = user
    return api_client
