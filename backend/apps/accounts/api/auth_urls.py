from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.api.views.auth_views import GuestLoginView, LoginView, LogoutView, RegisterView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="accounts-register"),
    path("login/", LoginView.as_view(), name="accounts-login"),
    path("logout/", LogoutView.as_view(), name="accounts-logout"),
    path("guest/", GuestLoginView.as_view(), name="accounts-guest"),
    path("token/refresh/", TokenRefreshView.as_view(), name="accounts-token-refresh"),
]
