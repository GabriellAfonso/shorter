from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.api.views.auth_views import LoginView, LogoutView, RegisterView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="accounts-register"),
    path("login/", LoginView.as_view(), name="accounts-login"),
    path("logout/", LogoutView.as_view(), name="accounts-logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="accounts-token-refresh"),
]
