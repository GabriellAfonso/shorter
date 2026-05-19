"""Business logic for user management."""

import logging
import secrets
import uuid

from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

logger = logging.getLogger(__name__)
User = get_user_model()

GUEST_EMAIL_DOMAIN = "guest.local"
GUEST_EMAIL_PREFIX = "guest_"


def create_user(*, email: str, password: str, first_name: str = "", last_name: str = ""):
    """
    Register a new user account.
    Raises ValidationError if the email is already taken.
    """

    user = User.objects.create_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
    )
    logger.info("New user registered: %s (id=%s)", email, user.pk)
    return user


def create_guest_user():
    """
    Create an ephemeral guest account with a random email + password.
    The password is discarded after creation (login is via JWT only).
    """
    email = f"{GUEST_EMAIL_PREFIX}{uuid.uuid4().hex}@{GUEST_EMAIL_DOMAIN}"
    password = secrets.token_urlsafe(32)
    user = User.objects.create_user(
        email=email,
        password=password,
        is_guest=True,
    )
    logger.info("New guest user created: %s (id=%s)", email, user.pk)
    return user


def update_user(
    *,
    user,
    first_name: str | None = None,
    last_name: str | None = None,
    bio: str | None = None,
    avatar_url: str | None = None,
):
    """Update mutable profile fields. Only provided (non-None) fields are updated."""
    updated_fields = []

    if first_name is not None:
        user.first_name = first_name
        updated_fields.append("first_name")
    if last_name is not None:
        user.last_name = last_name
        updated_fields.append("last_name")
    if bio is not None:
        user.bio = bio
        updated_fields.append("bio")
    if avatar_url is not None:
        user.avatar_url = avatar_url
        updated_fields.append("avatar_url")

    if updated_fields:
        user.save(update_fields=updated_fields + ["updated_at"])

    return user


def change_password(*, user, old_password: str, new_password: str) -> None:
    """Change a user's password after verifying the current one."""
    if not user.check_password(old_password):
        raise ValidationError({"old_password": "Current password is incorrect."})
    user.set_password(new_password)
    user.save(update_fields=["password", "updated_at"])

    from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

    for token in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=token)

    logger.info("Password changed for user %s — all tokens invalidated", user.email)
