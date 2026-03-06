from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    links_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "bio",
            "avatar_url",
            "links_count",
            "date_joined",
            "created_at",
        )
        read_only_fields = ("id", "email", "date_joined", "created_at", "full_name", "links_count")

    def get_links_count(self, obj) -> int:
        return obj.short_urls.filter(is_active=True).count()


_NAME_FIELD_ERRORS = {"max_length": _("Max {max_length} characters.")}
_PASS_FIELD_ERRORS = {
    "min_length": _("Password must be at least {min_length} characters."),
    "max_length": _("Password must be at most {max_length} characters."),
}


class UpdateProfileSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=50, required=False, error_messages=_NAME_FIELD_ERRORS)
    last_name = serializers.CharField(max_length=50, required=False, error_messages=_NAME_FIELD_ERRORS)
    bio = serializers.CharField(max_length=500, allow_blank=True, required=False)
    avatar_url = serializers.URLField(allow_blank=True, required=False)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, min_length=6, max_length=128, error_messages=_PASS_FIELD_ERRORS)
    new_password = serializers.CharField(write_only=True, min_length=6, max_length=128, error_messages=_PASS_FIELD_ERRORS)
    confirm_password = serializers.CharField(write_only=True, min_length=6, max_length=128, error_messages=_PASS_FIELD_ERRORS)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": _("Passwords do not match.")})
        return attrs
