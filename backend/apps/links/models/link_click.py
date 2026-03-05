"""LinkClick model — append-only analytics record per redirect."""
from django.db import models


class LinkClick(models.Model):
    link = models.ForeignKey(
        "links.ShortURL",
        on_delete=models.CASCADE,
        related_name="clicks",
    )
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    # Store a hashed/anonymised IP for GDPR compliance.
    ip_address = models.CharField(max_length=64, blank=True)
    user_agent = models.TextField(blank=True)
    referrer = models.URLField(max_length=2048, blank=True)
    country = models.CharField(max_length=100, blank=True)
    # Parsed from user_agent
    browser = models.CharField(max_length=100, blank=True)
    os = models.CharField(max_length=100, blank=True)
    device_type = models.CharField(max_length=50, blank=True)  # desktop | mobile | tablet | bot

    class Meta:
        db_table = "link_clicks"
        verbose_name = "Link Click"
        verbose_name_plural = "Link Clicks"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["link", "timestamp"], name="link_clicks_link_ts_idx"),
            models.Index(fields=["link", "device_type"], name="link_clicks_link_device_idx"),
        ]

    def __str__(self) -> str:
        return f"Click on {self.link.slug} at {self.timestamp}"
