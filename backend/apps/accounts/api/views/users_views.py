"""Thin views — all logic delegated to services/selectors."""
import logging
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.api.serializers.users_serializers import ChangePasswordSerializer, UpdateProfileSerializer, UserProfileSerializer
from apps.accounts.services.user_service import change_password, update_user

logger = logging.getLogger(__name__)


class MeView(APIView):
    """Retrieve the current authenticated user's profile."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)


class UpdateProfileView(APIView):
    """Partially update the authenticated user's profile."""

    permission_classes = [IsAuthenticated]

    def patch(self, request: Request) -> Response:
        serializer = UpdateProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = update_user(user=request.user, **serializer.validated_data)
        return Response(UserProfileSerializer(user).data)


class ChangePasswordView(APIView):
    """Change the authenticated user's password."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        change_password(
            user=request.user,
            old_password=serializer.validated_data["old_password"],
            new_password=serializer.validated_data["new_password"],
        )
        return Response({"detail": "Password updated successfully."}, status=status.HTTP_200_OK)
