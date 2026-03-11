"""Tests for core.views.HealthCheckView."""
from unittest.mock import patch

import pytest
from django.test import Client

pytestmark = pytest.mark.integration

HEALTH_URL = "/api/v1/health/"


@pytest.mark.django_db
class TestHealthCheckView:
    def setup_method(self, _method):
        self.client = Client()

    def test_returns_200_with_ok_status(self):
        response = self.client.get(HEALTH_URL)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["checks"]["db"]["status"] == "ok"
        assert data["checks"]["redis"]["status"] == "ok"

    def test_accessible_without_authentication(self):
        response = self.client.get(HEALTH_URL)
        assert response.status_code == 200

    def test_db_failure_returns_503_degraded(self):
        with patch("core.views.connection.cursor", side_effect=Exception("DB down")):
            response = self.client.get(HEALTH_URL)
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "degraded"
        assert data["checks"]["db"]["status"] == "error"

    def test_cache_failure_returns_503_degraded(self):
        with patch("core.views.cache.set", side_effect=Exception("Redis down")):
            response = self.client.get(HEALTH_URL)
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "degraded"
        assert data["checks"]["redis"]["status"] == "error"
