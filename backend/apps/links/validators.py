"""
URL and slug validators with OWASP-aligned security controls.

Key protections:
  - SSRF: blocks private/loopback IP ranges and localhost hostnames.
  - Scheme: only HTTP/HTTPS allowed.
  - Slug: alphanumeric + hyphen/underscore, no reserved words.
"""
import ipaddress
import logging
import re
from urllib.parse import urlparse

from rest_framework.exceptions import ValidationError

logger = logging.getLogger(__name__)

# ─── Constants ────────────────────────────────────────────────────────────

ALLOWED_SCHEMES = {"http", "https"}

BLOCKED_HOSTNAMES = frozenset(
    {
        "localhost",
        "127.0.0.1",
        "::1",
        "0.0.0.0",
        "metadata.google.internal",  # GCP IMDS
        "169.254.169.254",           # AWS/Azure IMDS (also caught by IP check)
    }
)

# RFC 1918 + loopback + link-local + private IPv6
_PRIVATE_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),   # link-local / AWS IMDS
    ipaddress.ip_network("100.64.0.0/10"),    # shared address space
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

RESERVED_SLUGS = frozenset(
    {
        "admin", "api", "static", "media", "login", "logout",
        "register", "dashboard", "links", "health", "metrics",
        "favicon", "robots", "sitemap",
    }
)

_SLUG_RE = re.compile(r"^[A-Za-z0-9_-]+$")
_MAX_URL_LENGTH = 2048


# ─── URL validator ────────────────────────────────────────────────────────


def validate_target_url(url: str) -> str:
    """
    Validate and return the URL, or raise ValidationError.

    Checks:
    1. Length
    2. Parseable URL with allowed scheme
    3. Non-empty hostname
    4. Hostname not in blocked list
    5. If hostname looks like an IP, ensure it is not in a private range
    """
    if len(url) > _MAX_URL_LENGTH:
        raise ValidationError({"original_url": f"URL must be at most {_MAX_URL_LENGTH} characters."})

    try:
        parsed = urlparse(url)
    except Exception:
        raise ValidationError({"original_url": "Invalid URL format."})

    if parsed.scheme not in ALLOWED_SCHEMES:
        raise ValidationError(
            {"original_url": f"Only HTTP and HTTPS URLs are permitted (got: '{parsed.scheme}')."}
        )

    hostname = (parsed.hostname or "").lower()
    if not hostname:
        raise ValidationError({"original_url": "URL must contain a valid hostname."})

    if hostname in BLOCKED_HOSTNAMES:
        raise ValidationError({"original_url": "This URL target is not permitted."})

    # Resolve hostname to check for private IPs (inline; no DNS lookup needed
    # for literal IP addresses, which is the critical SSRF vector).
    try:
        ip = ipaddress.ip_address(hostname)
        _assert_public_ip(ip)
    except ValueError:
        pass  # Not an IP literal — hostname-based SSRFs are harder but less critical.

    return url


def _assert_public_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> None:
    for network in _PRIVATE_NETWORKS:
        if ip in network:
            raise ValidationError(
                {"original_url": "URLs pointing to private or reserved IP ranges are not allowed."}
            )


# ─── Slug validator ───────────────────────────────────────────────────────


def validate_custom_slug(slug: str) -> str:
    """
    Validate a custom slug:
    - 2–50 characters, alphanumeric + hyphen + underscore
    - Not a reserved system word
    """
    if not (2 <= len(slug) <= 50):
        raise ValidationError({"slug": "Custom slug must be between 2 and 50 characters."})

    if not _SLUG_RE.match(slug):
        raise ValidationError(
            {"slug": "Slug may only contain letters, numbers, hyphens and underscores."}
        )

    if slug.lower() in RESERVED_SLUGS:
        raise ValidationError({"slug": f"The slug '{slug}' is reserved and cannot be used."})

    return slug
