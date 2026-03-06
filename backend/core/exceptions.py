"""
Custom exception handler and exception classes.
All API errors are normalised to:
  { "error": { "code": "...", "message": "...", "details": {...} } }
"""
import logging
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied, ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc: Exception, context: dict) -> Response | None:
    """Wrap DRF's default handler and normalise the error envelope."""
    # Convert Django exceptions to DRF ones.
    if isinstance(exc, DjangoValidationError):
        exc = ValidationError(detail=exc.message_dict if hasattr(exc, "message_dict") else exc.messages)
    elif isinstance(exc, ObjectDoesNotExist):
        exc = NotFound()
    elif isinstance(exc, PermissionDenied):
        from rest_framework.exceptions import PermissionDenied as DRFPermissionDenied
        exc = DRFPermissionDenied()

    response = drf_exception_handler(exc, context)

    if response is None:
        logger.exception("Unhandled exception", exc_info=exc)
        return Response(
            {"error": {"code": "internal_error", "message": _("An unexpected error occurred.")}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Normalise the response body.
    error_payload: dict = {"code": "error", "message": ""}

    if isinstance(exc, ValidationError):
        error_payload["code"] = "validation_error"
        error_payload["message"] = _("Invalid input.")
        error_payload["details"] = response.data
    elif hasattr(exc, "default_code"):
        error_payload["code"] = exc.default_code  # type: ignore[union-attr]
        error_payload["message"] = str(exc.detail) if hasattr(exc, "detail") else str(exc)
    else:
        error_payload["message"] = str(response.data)

    response.data = {"error": error_payload}
    return response


# ─── Custom exception classes ──────────────────────────────────────────────

class NotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = _("Resource not found.")
    default_code = "not_found"


class ConflictError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = _("A resource with this identifier already exists.")
    default_code = "conflict"


class ServiceUnavailable(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = _("Service temporarily unavailable.")
    default_code = "service_unavailable"


class RateLimitExceeded(APIException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = _("Rate limit exceeded. Please slow down.")
    default_code = "rate_limit_exceeded"


class QuotaExceeded(APIException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = _("You have reached the maximum number of active links. Delete some links to create new ones.")
    default_code = "quota_exceeded"
