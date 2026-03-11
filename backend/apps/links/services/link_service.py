"""
Business logic for the links feature.

Design decisions:
- URL validated against SSRF / scheme / length rules before persistence.
- Custom slugs validated against reserved-word list.
- Slug generation uses `secrets.choice` (cryptographically secure base-62).
- Redis cache is populated on first redirect and invalidated on deactivation/deletion.
- Analytics cache is invalidated when a link is deleted.
- Click logging is intentionally async (Celery) so the redirect is never blocked.
"""
import logging
from datetime import datetime

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.db.models import F
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from apps.links.models.link_click import LinkClick
from apps.links.models.short_url import ShortURL
from apps.links.selectors.link_selector import invalidate_analytics_cache, slug_exists
from apps.links.validators import validate_custom_slug, validate_target_url
from core.exceptions import QuotaExceeded
from core.utils import generate_slug, hash_ip

logger = logging.getLogger(__name__)

REDIRECT_CACHE_KEY = "redirect:{slug}"


def _cache_key(slug: str) -> str:
    return REDIRECT_CACHE_KEY.format(slug=slug)


# ─── Public service functions ─────────────────────────────────────────────


def create_short_url(
    *,
    original_url: str,
    owner,
    custom_slug: str | None = None,
    title: str = "",
    expires_at: datetime | None = None,
) -> ShortURL:
    """
    Create and persist a new ShortURL.

    If `custom_slug` is provided it is validated for uniqueness.
    Otherwise a random slug is generated (up to 5 retries on collision).
    """
    # ── Quota: enforce per-user active link limit ────────────────────────────
    max_links = getattr(settings, "MAX_LINKS_PER_USER", 30)
    active_count = ShortURL.objects.filter(owner=owner, is_active=True).count()
    if active_count >= max_links:
        raise QuotaExceeded(
            _("You have reached the limit of %(n)s active links. Delete some links to create new ones.") % {"n": max_links}
        )

    # ── Security: validate target URL (SSRF / scheme / length) ─────────────
    validate_target_url(original_url)

    if custom_slug:
        validate_custom_slug(custom_slug)
        if slug_exists(custom_slug):
            raise ValidationError({"slug": _("The slug '%(slug)s' is already taken.") % {"slug": custom_slug}})
        slug = custom_slug
    else:
        slug = _generate_unique_slug()

    link = ShortURL.objects.create(
        original_url=original_url,
        slug=slug,
        owner=owner,
        title=title or _infer_title(original_url),
        expires_at=expires_at,
    )
    logger.info("Created short URL %s → %s (owner=%s)", slug, original_url[:60], owner.email)
    return link


def delete_short_url(*, link: ShortURL) -> None:
    """Soft-delete a link and purge all related cache entries."""
    cache.delete(_cache_key(link.slug))
    invalidate_analytics_cache(str(link.id))
    link.is_active = False
    link.save(update_fields=["is_active", "updated_at"])
    logger.info("Deactivated link %s", link.slug)


def get_redirect_url(slug: str) -> tuple[str, str] | None:
    """
    Return (destination_url, link_id) for a slug with Redis-backed caching.
    Returns None if not found or expired.

    Both values are cached together so the redirect view never needs a
    second DB query to obtain the link id for async click logging.
    """
    key = _cache_key(slug)
    cached = cache.get(key)
    if cached is not None:
        return cached["url"], cached["id"]

    from apps.links.selectors.link_selector import get_link_by_slug
    from core.exceptions import NotFound

    try:
        link = get_link_by_slug(slug)
    except NotFound:
        return None

    ttl = _compute_ttl(link)
    cache.set(key, {"url": link.original_url, "id": str(link.id)}, ttl)
    return link.original_url, str(link.id)


def record_click(
    *,
    link_id: str,
    ip_address: str,
    user_agent: str,
    referrer: str,
) -> None:
    """
    Persist a LinkClick and atomically increment click_count.
    Called from the Celery task — should NOT be called from the request path.
    """
    try:
        link = ShortURL.objects.get(pk=link_id)
    except ShortURL.DoesNotExist:
        logger.warning("record_click: link %s not found, skipping.", link_id)
        return

    device_info = _parse_user_agent(user_agent)
    hashed_ip = hash_ip(ip_address) if ip_address else ""

    with transaction.atomic():
        LinkClick.objects.create(
            link=link,
            ip_address=hashed_ip,
            user_agent=user_agent[:500],
            referrer=referrer[:2048],
            browser=device_info["browser"],
            os=device_info["os"],
            device_type=device_info["device_type"],
        )
        ShortURL.objects.filter(pk=link_id).update(click_count=F("click_count") + 1)


# ─── Private helpers ──────────────────────────────────────────────────────


def _generate_unique_slug(max_retries: int = 5) -> str:
    length = getattr(settings, "SHORT_URL_LENGTH", 8)
    for attempt in range(max_retries):
        slug = generate_slug(length)
        if not slug_exists(slug):
            return slug
        logger.debug("Slug collision on attempt %d: %s", attempt + 1, slug)
    raise ValidationError({"slug": _("Could not generate a unique slug. Please try again.")})


def _compute_ttl(link: ShortURL) -> int:
    """Return cache TTL in seconds, capped by expiry if set."""
    default_ttl = getattr(settings, "REDIRECT_CACHE_TTL", 86400)
    if link.expires_at:
        from django.utils import timezone
        remaining = int((link.expires_at - timezone.now()).total_seconds())
        return max(1, min(remaining, default_ttl))
    return default_ttl


def _infer_title(url: str) -> str:
    """Best-effort title from URL (just the domain)."""
    try:
        from urllib.parse import urlparse
        return urlparse(url).netloc
    except Exception:
        return ""


def _parse_user_agent(ua_string: str) -> dict:
    """Parse user-agent string into device metadata."""
    try:
        import user_agents
        ua = user_agents.parse(ua_string)
        if ua.is_bot:
            device_type = "bot"
        elif ua.is_mobile:
            device_type = "mobile"
        elif ua.is_tablet:
            device_type = "tablet"
        else:
            device_type = "desktop"
        return {
            "browser": ua.browser.family[:100],
            "os": ua.os.family[:100],
            "device_type": device_type,
        }
    except Exception:
        return {"browser": "", "os": "", "device_type": "unknown"}
