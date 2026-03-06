"""
Celery tasks for the links feature.
All heavy/async operations go here so the redirect path stays fast.
"""
import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="apps.links.tasks.log_click",
    max_retries=3,
    default_retry_delay=5,
    queue="clicks",
    acks_late=True,
)
def log_click(
    self,
    link_id: str,
    ip_address: str,
    user_agent: str,
    referrer: str,
) -> None:
    """
    Persist a click record asynchronously so the redirect response
    is not blocked by DB writes.
    """
    try:
        from apps.links.services.link_service import record_click
        record_click(
            link_id=link_id,
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=referrer,
        )
    except Exception as exc:
        logger.warning("log_click task failed (attempt %s): %s", self.request.retries, exc)
        raise self.retry(exc=exc)


@shared_task(name="apps.links.tasks.deactivate_expired_links")
def deactivate_expired_links() -> int:
    """
    Periodic task: set is_active=False for all expired links.
    Invalidates Redis cache for each affected slug before the update
    so redirect cache does not serve stale data.
    Scheduled via django-celery-beat.
    """
    from django.core.cache import cache
    from django.utils import timezone
    from apps.links.models.short_url import ShortURL

    expired_qs = ShortURL.objects.filter(
        is_active=True,
        expires_at__lt=timezone.now(),
    )

    slugs = list(expired_qs.values_list("slug", flat=True))
    if slugs:
        cache.delete_many([f"redirect:{slug}" for slug in slugs])

    updated = expired_qs.update(is_active=False)

    logger.info("Deactivated %d expired links, cleared %d cache entries.", updated, len(slugs))
    return updated
