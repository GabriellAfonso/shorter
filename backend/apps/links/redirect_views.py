"""
Fast redirect view — plain Django (no DRF serialisation overhead).

Security additions (Part 2):
  - Redis sliding-window rate limit per client IP (REDIRECT_RATE_LIMIT req/min).
  - Structured 429 response with Retry-After header.
  - Slug validated at URL-conf level (regex in redirect_urls.py).

Flow:
  1. Rate-limit check  (Redis INCR/EXPIRE pipeline, O(1)).
  2. Cache lookup       (Redis GET, O(1)).
  3. On miss → DB query, populate cache.
  4. Fire Celery task to log click (non-blocking).
  5. Return HTTP 302.
"""
import logging
from django.conf import settings
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import never_cache

from apps.links.services.link_service import get_redirect_url
from apps.links.tasks import log_click
from core.utils import get_client_ip

logger = logging.getLogger(__name__)

_RATE_WINDOW = 60  # seconds


def _get_rate_limit() -> int:
    return getattr(settings, "REDIRECT_RATE_LIMIT", 200)


def _is_rate_limited(ip: str) -> bool:
    """
    Sliding-window rate limiter using Redis INCR + EXPIRE.
    Returns True when the caller exceeds the configured limit.
    Degrades gracefully to allow requests if Redis is unreachable.
    """
    try:
        from django_redis import get_redis_connection
        redis = get_redis_connection("default")
        key = f"rl:redirect:{ip}"
        pipe = redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, _RATE_WINDOW)
        count, _ = pipe.execute()
        return int(count) > _get_rate_limit()
    except Exception:
        logger.warning("Rate-limit Redis check failed; allowing request through.")
        return False


@method_decorator(never_cache, name="dispatch")
class RedirectView(View):
    def get(self, request, slug: str) -> HttpResponse:
        ip = get_client_ip(request) or "unknown"

        if _is_rate_limited(ip):
            return HttpResponse(
                b"<h1>429 \xe2\x80\x94 Too Many Requests</h1>",
                status=429,
                content_type="text/html; charset=utf-8",
                headers={"Retry-After": str(_RATE_WINDOW)},
            )

        destination = get_redirect_url(slug)

        if destination is None:
            return HttpResponseNotFound(
                b"<h1>404 \xe2\x80\x94 Short URL not found or has expired.</h1>",
                content_type="text/html; charset=utf-8",
            )

        # Async click logging — does NOT block the redirect response.
        try:
            from apps.links.models import ShortURL
            link = ShortURL.objects.only("id").get(slug=slug, is_active=True)
            log_click.delay(
                link_id=str(link.id),
                ip_address=ip,
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
                referrer=request.META.get("HTTP_REFERER", "")[:2048],
            )
        except Exception:
            logger.exception("Failed to dispatch log_click for slug=%s", slug)

        return HttpResponseRedirect(destination)
