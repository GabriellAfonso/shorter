"""Read-only database queries for the users domain."""
import logging
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from core.exceptions import NotFound

logger = logging.getLogger(__name__)
User = get_user_model()


def get_user_by_id(user_id: int):
    """Return a User or raise NotFound."""
    try:
        return User.objects.get(pk=user_id)
    except ObjectDoesNotExist:
        raise NotFound(f"User with id={user_id} not found.")


def get_user_by_email(email: str):
    """Return a User by email or raise NotFound."""
    try:
        return User.objects.get(email__iexact=email)
    except ObjectDoesNotExist:
        raise NotFound(f"User with email={email} not found.")


def user_exists(email: str) -> bool:
    return User.objects.filter(email__iexact=email).exists()
