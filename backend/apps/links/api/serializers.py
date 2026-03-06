from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from apps.links.models.short_url import ShortURL


class ShortURLSerializer(serializers.ModelSerializer):
    short_url = serializers.CharField(read_only=True)
    owner_email = serializers.EmailField(source="owner.email", read_only=True)
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = ShortURL
        fields = (
            "id",
            "original_url",
            "slug",
            "title",
            "short_url",
            "owner_email",
            "is_active",
            "is_expired",
            "click_count",
            "created_at",
            "expires_at",
        )
        read_only_fields = ("id", "click_count", "created_at", "is_active", "owner_email", "short_url", "is_expired")


class CreateShortURLSerializer(serializers.Serializer):
    original_url = serializers.URLField(
        max_length=settings.MAX_TARGET_URL_LENGTH,
        help_text="Target URL (HTTP/HTTPS only). Private IP ranges are blocked.",
    )
    slug = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        default="",
        help_text="Optional custom slug. Letters, numbers, hyphens and underscores only.",
    )
    title = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")
    expires_at = serializers.DateTimeField(required=False, allow_null=True)

    def validate_original_url(self, value: str) -> str:
        from apps.links.validators import validate_target_url
        return validate_target_url(value)

    def validate_expires_at(self, value):
        if value and value <= timezone.now():
            raise serializers.ValidationError(_("Expiry date must be in the future."))
        return value

    def validate_slug(self, value: str) -> str | None:
        stripped = value.strip()
        if not stripped:
            return None
        from apps.links.validators import validate_custom_slug
        return validate_custom_slug(stripped)


class AnalyticsSerializer(serializers.Serializer):
    total_clicks = serializers.IntegerField()
    clicks_in_period = serializers.IntegerField()
    period_days = serializers.IntegerField()
    daily_clicks = serializers.ListField()
    by_device = serializers.ListField()
    top_referrers = serializers.ListField()
