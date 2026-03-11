"""
Tests for URL and slug validators (SSRF, scheme, slug rules).
"""
import pytest

pytestmark = pytest.mark.unit
from rest_framework.exceptions import ValidationError

from apps.links.validators import validate_custom_slug, validate_target_url


class TestValidateTargetURL:
    def test_valid_http_url_passes(self):
        assert validate_target_url("http://example.com") == "http://example.com"

    def test_valid_https_url_passes(self):
        assert validate_target_url("https://github.com/some/repo") == "https://github.com/some/repo"

    def test_javascript_scheme_blocked(self):
        with pytest.raises(ValidationError):
            validate_target_url("javascript:alert(1)")

    def test_ftp_scheme_blocked(self):
        with pytest.raises(ValidationError):
            validate_target_url("ftp://files.example.com")

    def test_data_scheme_blocked(self):
        with pytest.raises(ValidationError):
            validate_target_url("data:text/html,<h1>xss</h1>")

    def test_localhost_blocked(self):
        with pytest.raises(ValidationError):
            validate_target_url("http://localhost/admin")

    def test_loopback_ip_blocked(self):
        with pytest.raises(ValidationError):
            validate_target_url("http://127.0.0.1/secret")

    def test_private_class_a_blocked(self):
        with pytest.raises(ValidationError):
            validate_target_url("http://10.0.0.1/internal")

    def test_private_class_b_blocked(self):
        with pytest.raises(ValidationError):
            validate_target_url("http://172.16.5.10/api")

    def test_private_class_c_blocked(self):
        with pytest.raises(ValidationError):
            validate_target_url("http://192.168.1.1/router")

    def test_aws_imds_blocked(self):
        with pytest.raises(ValidationError):
            validate_target_url("http://169.254.169.254/latest/meta-data/")

    def test_url_too_long_blocked(self):
        long_url = "https://example.com/" + "a" * 2048
        with pytest.raises(ValidationError):
            validate_target_url(long_url)

    def test_missing_hostname_blocked(self):
        with pytest.raises(ValidationError):
            validate_target_url("https:///no-hostname")


class TestValidateCustomSlug:
    def test_valid_alphanumeric_slug(self):
        assert validate_custom_slug("hello123") == "hello123"

    def test_slug_with_hyphen(self):
        assert validate_custom_slug("my-link") == "my-link"

    def test_slug_with_underscore(self):
        assert validate_custom_slug("my_link") == "my_link"

    def test_slug_too_short_blocked(self):
        with pytest.raises(ValidationError):
            validate_custom_slug("a")

    def test_slug_too_long_blocked(self):
        with pytest.raises(ValidationError):
            validate_custom_slug("a" * 51)

    def test_slug_with_spaces_blocked(self):
        with pytest.raises(ValidationError):
            validate_custom_slug("my link")

    def test_reserved_slug_admin_blocked(self):
        with pytest.raises(ValidationError):
            validate_custom_slug("admin")

    def test_reserved_slug_api_blocked(self):
        with pytest.raises(ValidationError):
            validate_custom_slug("api")

    def test_reserved_slug_login_blocked(self):
        with pytest.raises(ValidationError):
            validate_custom_slug("login")

    def test_special_chars_blocked(self):
        with pytest.raises(ValidationError):
            validate_custom_slug("my/link")
