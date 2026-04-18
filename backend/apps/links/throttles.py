"""
Custom DRF throttle classes for the links feature.

UserRateThrottle subclasses are used for authenticated endpoints so the
scope is fixed at the class level. ScopedRateThrottle is intentionally
avoided here: its allow_request() overrides self.scope from view.throttle_scope
which these views do not set, causing the throttle to silently allow all requests.

Redis-based redirect rate limiting is implemented separately in
`redirect_views.py` using a sliding-window counter via django-redis,
because the redirect endpoint is a plain Django view (not DRF).
"""

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class LinkCreateThrottle(UserRateThrottle):
    """
    Tight rate limit on link creation — prevents slug-exhaustion attacks.
    Configured via REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']['link_create'].
    """

    scope = "link_create"


class LinkAnalyticsThrottle(UserRateThrottle):
    """
    Analytics reads are heavier DB/cache operations; cap per user.
    """

    scope = "link_analytics"


class AuthRateThrottle(AnonRateThrottle):
    """
    IP-based rate limit for authentication endpoints (register, login).
    Prevents brute-force and account creation abuse.
    Configured via REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']['auth'].
    """

    scope = "auth"
