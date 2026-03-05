"""Redirect endpoint URL configuration (registered at root in config/auth_urls.py)."""
from django.urls import path
from apps.links.redirect_views import RedirectView

urlpatterns = [
    path("", RedirectView.as_view(), name="redirect"),
]
