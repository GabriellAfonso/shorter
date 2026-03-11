"""
Tests for config/settings/production.py:
 - fail-fast on missing SECRET_KEY or SHORT_URL_BASE_DOMAIN
 - CORS_ALLOWED_ORIGINS parsing never produces ['']
"""
import importlib
import sys
from unittest.mock import patch

import pytest
from django.core.exceptions import ImproperlyConfigured

MODULE = "config.settings.production"

VALID_ENV = {
    "SECRET_KEY": "test-secret-key-at-least-50-chars-long-for-safety",
    "SHORT_URL_BASE_DOMAIN": "https://example.com",
}


def _import_production(env: dict):
    """Pop cached module and re-import production settings with the given env."""
    sys.modules.pop(MODULE, None)
    with patch.dict("os.environ", env, clear=True):
        return importlib.import_module(MODULE)


@pytest.mark.unit
class TestProductionSettingsFailFast:
    def teardown_method(self, _method):
        sys.modules.pop(MODULE, None)

    def test_missing_secret_key_raises(self):
        env = {"SHORT_URL_BASE_DOMAIN": "https://example.com"}
        with pytest.raises(ImproperlyConfigured, match="SECRET_KEY"):
            _import_production(env)

    def test_empty_secret_key_raises(self):
        env = {"SECRET_KEY": "", "SHORT_URL_BASE_DOMAIN": "https://example.com"}
        with pytest.raises(ImproperlyConfigured, match="SECRET_KEY"):
            _import_production(env)

    def test_missing_short_url_base_domain_raises(self):
        env = {"SECRET_KEY": "test-secret-key-at-least-50-chars-long-for-safety"}
        with pytest.raises(ImproperlyConfigured, match="SHORT_URL_BASE_DOMAIN"):
            _import_production(env)

    def test_empty_short_url_base_domain_raises(self):
        env = {
            "SECRET_KEY": "test-secret-key-at-least-50-chars-long-for-safety",
            "SHORT_URL_BASE_DOMAIN": "",
        }
        with pytest.raises(ImproperlyConfigured, match="SHORT_URL_BASE_DOMAIN"):
            _import_production(env)

    def test_both_vars_set_loads_successfully(self):
        mod = _import_production(VALID_ENV)
        assert mod.SECRET_KEY == VALID_ENV["SECRET_KEY"]
        assert mod.SHORT_URL_BASE_DOMAIN == VALID_ENV["SHORT_URL_BASE_DOMAIN"]
        assert mod.DEBUG is False


@pytest.mark.unit
class TestCorsAllowedOrigins:
    def teardown_method(self, _method):
        sys.modules.pop(MODULE, None)

    def _load_cors(self, cors_env_value=None):
        env = dict(VALID_ENV)
        if cors_env_value is not None:
            env["CORS_ALLOWED_ORIGINS"] = cors_env_value
        return _import_production(env).CORS_ALLOWED_ORIGINS

    def test_not_set_returns_empty_list(self):
        assert self._load_cors() == []

    def test_empty_string_returns_empty_list(self):
        assert self._load_cors("") == []

    def test_single_origin(self):
        assert self._load_cors("https://example.com") == ["https://example.com"]

    def test_multiple_origins_comma_separated(self):
        result = self._load_cors("https://a.com,https://b.com")
        assert result == ["https://a.com", "https://b.com"]

    def test_extra_whitespace_is_stripped(self):
        result = self._load_cors(" https://a.com , https://b.com ")
        assert result == ["https://a.com", "https://b.com"]
