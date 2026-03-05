from django.contrib import admin
from apps.links.models.link_click import LinkClick
from apps.links.models.short_url import ShortURL


@admin.register(ShortURL)
class ShortURLAdmin(admin.ModelAdmin):
    list_display = ("slug", "owner", "original_url_truncated", "click_count", "is_active", "created_at", "expires_at")
    list_filter = ("is_active",)
    search_fields = ("slug", "owner__email", "title", "original_url")
    readonly_fields = ("id", "click_count", "created_at", "updated_at")
    raw_id_fields = ("owner",)

    @admin.display(description="Original URL")
    def original_url_truncated(self, obj):
        return obj.original_url[:80] + "..." if len(obj.original_url) > 80 else obj.original_url


@admin.register(LinkClick)
class LinkClickAdmin(admin.ModelAdmin):
    list_display = ("link", "timestamp", "device_type", "country", "browser")
    list_filter = ("device_type",)
    search_fields = ("link__slug",)
    readonly_fields = ("timestamp",)
    raw_id_fields = ("link",)
