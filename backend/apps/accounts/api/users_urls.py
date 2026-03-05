from django.urls import path
from apps.accounts.api.views.users_views import ChangePasswordView, MeView, UpdateProfileView

urlpatterns = [
    path("me/", MeView.as_view(), name="users-me"),
    path("me/update/", UpdateProfileView.as_view(), name="users-update-profile"),
    path("me/change-password/", ChangePasswordView.as_view(), name="users-change-password"),
]
