"""Shared utility functions."""
import hashlib
import secrets
import string

SLUG_ALPHABET = string.ascii_letters + string.digits  # base62, 62 chars


def generate_slug(length: int = 8) -> str:
    """
    Generate a cryptographically secure random slug.
    Uses base-62 alphabet (a-z, A-Z, 0-9).
    For length=8 there are 62^8 ≈ 218 trillion possibilities.
    """
    return "".join(secrets.choice(SLUG_ALPHABET) for _ in range(length))


def get_client_ip(request) -> str | None:
    """Extract the real client IP, honouring X-Forwarded-For."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        # Take the first (original client) IP
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def hash_ip(ip: str) -> str:
    """One-way hash an IP address for privacy-safe storage."""
    return hashlib.sha256(ip.encode()).hexdigest()[:32]
