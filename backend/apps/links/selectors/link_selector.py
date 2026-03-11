"""Read-only database queries for the links domain."""
import logging
from django.core.cache import cache
from django.db.models import Count, Q, QuerySet, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from core.exceptions import NotFound
from apps.links.models.link_click import LinkClick
from apps.links.models.short_url import ShortURL

logger = logging.getLogger(__name__)


_ANALYTICS_CACHE_TTL = 30
_ANALYTICS_CACHE_KEY = "analytics:{link_id}:{days}"


def get_link_by_slug(slug: str) -> ShortURL:
    """Return an active, non-expired ShortURL or raise NotFound."""
    try:
        link = ShortURL.objects.select_related("owner").get(slug=slug, is_active=True)
    except ShortURL.DoesNotExist:
        raise NotFound(f"No active link found for slug '{slug}'.")

    if link.is_expired:
        raise NotFound(f"The link '{slug}' has expired.")

    return link


def get_link_by_id(link_id: str, owner=None) -> ShortURL:
    """Return a ShortURL by UUID. Optionally scope to an owner."""
    qs = ShortURL.objects.select_related("owner")
    if owner is not None:
        qs = qs.filter(owner=owner)
    try:
        return qs.get(pk=link_id)
    except ShortURL.DoesNotExist:
        raise NotFound("Link not found.")


def get_user_links(user, is_active: bool | None = None) -> QuerySet:
    """Return a queryset of the user's links, optionally filtered by active status."""
    qs = ShortURL.objects.filter(owner=user).select_related("owner")
    if is_active is not None:
        qs = qs.filter(is_active=is_active)
    return qs


def get_link_analytics(link: ShortURL, days: int = 30) -> dict:
    """Aggregate analytics for a single link over the last N days (uncached)."""
    since = timezone.now() - timezone.timedelta(days=days)
    clicks_qs = LinkClick.objects.filter(link=link, timestamp__gte=since)

    daily = (
        clicks_qs
        .annotate(date=TruncDate("timestamp"))
        .values("date")
        .annotate(count=Count("id"))
        .order_by("date")
    )

    by_device = (
        clicks_qs
        .values("device_type")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    by_referrer = (
        clicks_qs
        .exclude(referrer="")
        .values("referrer")
        .annotate(count=Count("id"))
        .order_by("-count")[:10]
    )

    return {
        "total_clicks": link.click_count,
        "clicks_in_period": clicks_qs.count(),
        "period_days": days,
        "daily_clicks": list(daily),
        "by_device": list(by_device),
        "top_referrers": list(by_referrer),
    }


def get_cached_link_analytics(link: ShortURL, days: int = 30) -> dict:
    """
    Redis-cached wrapper around `get_link_analytics`.

    Cache key includes link ID and period so different day-ranges are
    stored separately. Invalidated automatically by TTL (5 minutes).
    Cache is also invalidated on link deletion via `delete_short_url`.
    """
    key = _ANALYTICS_CACHE_KEY.format(link_id=str(link.id), days=days)
    cached = cache.get(key)
    if cached is not None:
        return cached

    result = get_link_analytics(link, days=days)
    cache.set(key, result, _ANALYTICS_CACHE_TTL)
    return result


def invalidate_analytics_cache(link_id: str) -> None:
    """Evict all analytics cache entries for a given link."""
    for days in (7, 30, 90, 365):
        key = _ANALYTICS_CACHE_KEY.format(link_id=link_id, days=days)
        cache.delete(key)


def get_user_link_stats(user) -> dict:
    """
    Return aggregate stats for all of a user's links (active and inactive).

    - total_clicks: sum of click_count across every link the user ever created.
    - active_count: links that are active and not expired right now.
    """
    qs = ShortURL.objects.filter(owner=user)
    total_clicks = qs.aggregate(total=Sum("click_count"))["total"] or 0
    active_count = qs.filter(
        is_active=True,
    ).filter(
        Q(expires_at__isnull=True) | Q(expires_at__gte=timezone.now())
    ).count()
    return {"total_clicks": total_clicks, "active_count": active_count}


def slug_exists(slug: str) -> bool:
    return ShortURL.objects.filter(slug=slug).exists()
