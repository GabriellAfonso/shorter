from typing import Any, Dict
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        min_length=6,
        max_length=128,
        error_messages={
            "min_length": _("Password must be at least {min_length} characters."),
            "max_length": _("Password must be at most {max_length} characters."),
        },
    )
    first_name = serializers.CharField(
        max_length=50,
        required=False,
        default="",
        error_messages={"max_length": _("Max {max_length} characters.")},
    )
    last_name = serializers.CharField(
        max_length=50,
        required=False,
        default="",
        error_messages={"max_length": _("Max {max_length} characters.")},
    )

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(_("A user with this email already exists."))
        return value.lower()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Extend the default JWT serializer to include basic user info."""

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        # Call super and explicitly type data as Dict[str, Any]
        # to resolve the 'str vs dict' type mismatch warning.
        data: Dict[str, Any] = super().validate(attrs)

        data["user"] = {
            "id": self.user.pk,
            "email": self.user.email,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "full_name": self.user.get_full_name(),
        }
        return data


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()