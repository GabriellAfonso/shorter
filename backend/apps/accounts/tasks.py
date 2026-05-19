"""Celery tasks for the accounts feature."""

import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(name="apps.accounts.tasks.purge_guest_accounts")
def purge_guest_accounts() -> int:
    """
    Periodic task: delete guest users older than GUEST_ACCOUNT_PURGE_HOURS.
    Cascades to ShortURL and LinkClick via FK on_delete=CASCADE.
    """
    User = get_user_model()
    max_age = getattr(settings, "GUEST_ACCOUNT_PURGE_HOURS", 48)
    cutoff = timezone.now() - timedelta(hours=max_age)

    qs = User.objects.filter(is_guest=True, created_at__lt=cutoff)
    deleted, _ = qs.delete()

    logger.info("Purged %d guest accounts older than %dh.", deleted, max_age)
    return deleted
