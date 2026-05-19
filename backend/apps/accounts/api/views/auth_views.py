"""Authentication views: register, login, logout, token refresh."""

import logging
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.accounts.api.serializers.auth_serializers import (
    CustomTokenObtainPairSerializer,
    LogoutSerializer,
    RegisterSerializer,
)
from apps.accounts.api.serializers.users_serializers import UserProfileSerializer
from apps.accounts.services.user_service import create_guest_user, create_user
from apps.links.throttles import AuthRateThrottle, GuestCreateThrottle

logger = logging.getLogger(__name__)


class RegisterView(APIView):
    """Create a new user account and return JWT tokens."""

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def get_throttles(self):
        return [AuthRateThrottle()]

    def post(self, request: Request) -> Response:
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        user = create_user(
            email=d["email"],
            password=d["password"],
            first_name=d.get("first_name", ""),
            last_name=d.get("last_name", ""),
        )

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserProfileSerializer(user).data,
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
            },
            status=status.HTTP_201_CREATED,
        )


class LogoutView(APIView):
    """Blacklist the refresh token to log out the user."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            token = RefreshToken(serializer.validated_data["refresh"])
            token.blacklist()
        except TokenError as exc:
            return Response(
                {"error": {"code": "invalid_token", "message": str(exc)}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)


class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def get_throttles(self):
        return [AuthRateThrottle()]


def _issue_tokens(user) -> dict:
    refresh = RefreshToken.for_user(user)
    return {
        "user": UserProfileSerializer(user).data,
        "tokens": {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        },
    }


class GuestLoginView(APIView):
    """
    Idempotent guest login.

    If the request carries a valid JWT for an existing guest user, the same
    user is reused (no new account is created, throttle still applies). The
    response always includes a fresh access/refresh pair so the caller can
    upgrade an expired pair without invoking /token/refresh/.

    Without a valid guest token, a new ephemeral User(is_guest=True) is
    created and rate-limited by GuestCreateThrottle (per IP).
    """

    permission_classes = [AllowAny]
    authentication_classes: list = []  # manual JWT inspection only

    def get_throttles(self):
        return [GuestCreateThrottle()]

    def post(self, request: Request) -> Response:
        existing = self._resolve_existing_guest(request)
        if existing is not None:
            return Response(_issue_tokens(existing), status=status.HTTP_200_OK)

        user = create_guest_user()
        return Response(_issue_tokens(user), status=status.HTTP_201_CREATED)

    @staticmethod
    def _resolve_existing_guest(request: Request):
        header = JWTAuthentication().get_header(request)
        if header is None:
            return None
        raw = JWTAuthentication().get_raw_token(header)
        if raw is None:
            return None
        try:
            validated = JWTAuthentication().get_validated_token(raw)
            user = JWTAuthentication().get_user(validated)
        except (InvalidToken, TokenError):
            return None
        if not getattr(user, "is_guest", False):
            return None
        return user


TokenRefreshView = TokenRefreshView
