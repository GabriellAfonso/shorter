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
