"""Root URL configuration."""
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from core.views import HealthCheckView
from apps.links.redirect_views import RedirectView

urlpatterns = [
    path("core/", admin.site.urls),
    path("robots.txt", lambda _: HttpResponse("User-agent: *\nDisallow: /s/\nDisallow: /api/\nDisallow: /core/\n", content_type="text/plain")),

    # ─── Health check (no accounts required) ───────────────────────────────────
    path("api/v1/health/", HealthCheckView.as_view(), name="health-check"),

    # ─── Versioned API ─────────────────────────────────────────────────────
    path("api/v1/auth/", include("apps.accounts.api.auth_urls")),
    path("api/v1/users/", include("apps.accounts.api.users_urls")),
    path("api/v1/links/", include("apps.links.api.urls")),

    # ─── API Documentation ──────────────────────────────────────────────────
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/schema/swagger-ui/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/schema/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),

    # ─── Redirect endpoint (must be last to avoid shadowing API routes) ────
    path("s/<str:slug>/", RedirectView.as_view(), name="slug-redirect"),
]
