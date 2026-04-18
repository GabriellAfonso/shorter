"""
Unit tests for redirect view internals.
Covers: _is_rate_limited Redis pipeline logic and graceful degradation.
"""

from unittest.mock import MagicMock, patch

import pytest

from apps.links.redirect_views import _is_rate_limited

pytestmark = pytest.mark.unit


class TestIsRateLimited:
    def _make_redis(self, count: int) -> MagicMock:
        pipe = MagicMock()
        pipe.execute.return_value = (count, True)
        redis = MagicMock()
        redis.pipeline.return_value = pipe
        return redis

    def test_below_limit_returns_false(self, settings):
        settings.REDIRECT_RATE_LIMIT = 10
        with patch("django_redis.get_redis_connection", return_value=self._make_redis(5)):
            assert _is_rate_limited("1.2.3.4") is False

    def test_at_limit_returns_false(self, settings):
        settings.REDIRECT_RATE_LIMIT = 10
        with patch("django_redis.get_redis_connection", return_value=self._make_redis(10)):
            assert _is_rate_limited("1.2.3.4") is False

    def test_over_limit_returns_true(self, settings):
        settings.REDIRECT_RATE_LIMIT = 10
        with patch("django_redis.get_redis_connection", return_value=self._make_redis(11)):
            assert _is_rate_limited("1.2.3.4") is True

    def test_redis_failure_allows_request_through(self):
        with patch("django_redis.get_redis_connection", side_effect=Exception("Redis down")):
            assert _is_rate_limited("1.2.3.4") is False

    def test_uses_ip_in_cache_key(self, settings):
        settings.REDIRECT_RATE_LIMIT = 200
        redis = self._make_redis(1)
        with patch("django_redis.get_redis_connection", return_value=redis):
            _is_rate_limited("10.0.0.1")
        pipe = redis.pipeline.return_value
        incr_call = pipe.incr.call_args[0][0]
        assert "10.0.0.1" in incr_call
