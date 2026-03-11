"""Production settings — hardened security, no debug."""
import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401, F403

DEBUG = False

# ─── Required environment variables ───────────────────────────────────────
_secret = os.environ.get("SECRET_KEY")
if not _secret:
    raise ImproperlyConfigured(
        "SECRET_KEY environment variable must be set in production."
    )
SECRET_KEY = _secret
SIMPLE_JWT["SIGNING_KEY"] = SECRET_KEY  # noqa: F405 — fix early capture in base.py

_base_domain = os.environ.get("SHORT_URL_BASE_DOMAIN")
if not _base_domain:
    raise ImproperlyConfigured(
        "SHORT_URL_BASE_DOMAIN environment variable must be set in production."
    )
SHORT_URL_BASE_DOMAIN = _base_domain

# ─── Security headers ──────────────────────────────────────────────────────
# nginx já faz o redirect HTTP→HTTPS; Django não deve fazer double-redirect
SECURE_SSL_REDIRECT = False
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = 31_536_000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# ─── CORS ─────────────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = [o.strip() for o in os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",") if o.strip()]
CORS_ALLOW_CREDENTIALS = True

# ─── API Docs — correct public server prefix behind nginx reverse proxy ────
# nginx strips /shorter before forwarding to Django, so Swagger UI must know
# the real public base to build "Try it out" request URLs correctly.
SPECTACULAR_SETTINGS = {
    "SERVERS": [{"url": "/shorter", "description": "Production"}],
}

# ─── Logging ───────────────────────────────────────────────────────────────
LOGGING = {
    **LOGGING,  # noqa: F405
    "loggers": {
        **LOGGING["loggers"],  # noqa: F405
        "django.request": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}

