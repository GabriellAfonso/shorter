"""ShortURL model — the core domain entity."""
import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


class ShortURL(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    original_url = models.URLField("original URL", max_length=2048)
    slug = models.CharField(max_length=50, unique=True, db_index=True)
    title = models.CharField(max_length=200, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="short_urls",
    )
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    click_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "short_urls"
        verbose_name = "Short URL"
        verbose_name_plural = "Short URLs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["owner", "-created_at"], name="short_urls_owner_created_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.slug} → {self.original_url[:60]}"

    @property
    def is_expired(self) -> bool:
        return bool(self.expires_at and self.expires_at < timezone.now())

    @property
    def short_url(self) -> str:
        base = getattr(settings, "SHORT_URL_BASE_DOMAIN", "http://localhost:8000")
        return f"{base}/s/{self.slug}"
