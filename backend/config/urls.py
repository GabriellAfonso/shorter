"""Root URL configuration."""
from django.contrib import admin
from django.urls import path, include, re_path
from core.views import HealthCheckView
from apps.links.redirect_views import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),

    # ─── Health check (no accounts required) ───────────────────────────────────
    path("api/v1/health/", HealthCheckView.as_view(), name="health-check"),

    # ─── Versioned API ─────────────────────────────────────────────────────
    path("api/v1/auth/", include("apps.accounts.api.auth_urls")),
    path("api/v1/users/", include("apps.accounts.api.users_urls")),
    path("api/v1/links/", include("apps.links.api.urls")),

    # ─── Redirect endpoint (must be last to avoid shadowing API routes) ────
    path("s/<str:slug>/", RedirectView.as_view(), name="slug-redirect"),
]
