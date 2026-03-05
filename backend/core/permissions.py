"""Custom DRF permission classes."""
from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """
    Object-level permission: allow access only to the owner of the object.
    The model instance is expected to have an `owner` attribute.
    """

    message = "You do not have permission to access this resource."

    def has_object_permission(self, request, view, obj) -> bool:
        return bool(request.user and request.user.is_authenticated and obj.owner == request.user)


class IsOwnerOrReadOnly(BasePermission):
    """Read-only for everyone; full access for the owner."""

    def has_object_permission(self, request, view, obj) -> bool:
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return bool(request.user and request.user.is_authenticated and obj.owner == request.user)
