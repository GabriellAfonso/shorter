"""
Custom DRF throttle classes for the links feature.

ScopedRateThrottle lets us apply different rates to different actions
(e.g., link creation is tighter than analytics reads) while still
sharing the same Redis-backed DRF throttle cache.

Redis-based redirect rate limiting is implemented separately in
`redirect_views.py` using a sliding-window counter via django-redis,
because the redirect endpoint is a plain Django view (not DRF).
"""
from rest_framework.throttling import ScopedRateThrottle, UserRateThrottle


class LinkCreateThrottle(ScopedRateThrottle):
    """
    Tight rate limit on link creation — prevents slug-exhaustion attacks.
    Configured via REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']['link_create'].
    """
    scope = "link_create"


class LinkAnalyticsThrottle(ScopedRateThrottle):
    """
    Analytics reads are heavier DB/cache operations; cap per user.
    """
    scope = "link_analytics"


class RedirectIpThrottle(UserRateThrottle):
    """
    Fallback DRF throttle — the redirect endpoint uses its own Redis
    counter, but this can be used on DRF-wrapped redirect helpers.
    """
    scope = "redirect"

    def get_cache_key(self, request, view):
        # Key by IP rather than user for anonymous redirects.
        ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}
