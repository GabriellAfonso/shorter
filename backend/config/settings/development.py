"""Development settings — debug enabled, relaxed security."""

from config.settings.base import *  # noqa: F401, F403

DEBUG = True

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
CORS_ALLOW_CREDENTIALS = True

# Expose browsable API in dev
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
]

# Relaxed throttling in dev (all scopes must be present — missing keys raise ImproperlyConfigured)
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {  # noqa: F405
    "anon": "1000/minute",
    "user": "5000/minute",
    "auth": "10/minute",
    "link_create": "100/minute",
    "link_analytics": "500/minute",
}

# Use synchronous in-memory cache for tests (override per-test if needed)
# Keep Redis in dev for realistic behaviour.
