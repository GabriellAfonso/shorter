from typing import Any, Dict
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(max_length=150, required=False, default="")
    last_name = serializers.CharField(max_length=150, required=False, default="")

    @staticmethod
    def validate_email(value: str) -> str:
        """Fixed the 'static' warning by adding the decorator."""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
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
            "full_name": self.user.get_full_name(),  # Ensure this method exists on your User model
        }
        return data


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()