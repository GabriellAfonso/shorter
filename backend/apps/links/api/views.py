"""Links API views — thin controllers, logic in services/selectors."""
import logging
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.links.api.serializers import AnalyticsSerializer, CreateShortURLSerializer, ShortURLSerializer
from apps.links.selectors.link_selector import get_cached_link_analytics, get_link_by_id, get_user_links
from apps.links.services.link_service import create_short_url, delete_short_url
from apps.links.throttles import LinkAnalyticsThrottle, LinkCreateThrottle
from core.pagination import StandardResultsPagination
from core.permissions import IsOwner

logger = logging.getLogger(__name__)


class LinkListCreateView(APIView):
    """
    GET  /api/v1/links/   → list authenticated user's links (paginated)
    POST /api/v1/links/   → create a new short URL (rate-limited: 20/min)
    """

    permission_classes = [IsAuthenticated]

    def get_throttles(self):
        # Apply tighter throttle only on write operations.
        if self.request.method == "POST":
            return [LinkCreateThrottle()]
        return super().get_throttles()

    def get(self, request: Request) -> Response:
        is_active_param = request.query_params.get("is_active")
        if is_active_param is not None:
            is_active = is_active_param.lower() == "true"
        else:
            is_active = True  # default: only return active links

        qs = get_user_links(request.user, is_active=is_active)
        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(ShortURLSerializer(page, many=True).data)

    def post(self, request: Request) -> Response:
        serializer = CreateShortURLSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        link = create_short_url(
            original_url=d["original_url"],
            owner=request.user,
            custom_slug=d.get("slug") or None,
            title=d.get("title", ""),
            expires_at=d.get("expires_at"),
        )
        return Response(ShortURLSerializer(link).data, status=status.HTTP_201_CREATED)


class LinkDetailView(APIView):
    """
    GET    /api/v1/links/{id}/ → retrieve a link
    DELETE /api/v1/links/{id}/ → soft-delete a link (owner only)
    """

    permission_classes = [IsAuthenticated, IsOwner]

    def get(self, request: Request, link_id: str) -> Response:
        link = get_link_by_id(link_id, owner=request.user)
        return Response(ShortURLSerializer(link).data)

    def delete(self, request: Request, link_id: str) -> Response:
        link = get_link_by_id(link_id, owner=request.user)
        self.check_object_permissions(request, link)
        delete_short_url(link=link)
        return Response(status=status.HTTP_204_NO_CONTENT)


class LinkAnalyticsView(APIView):
    """GET /api/v1/links/{id}/analytics/?days=30"""

    permission_classes = [IsAuthenticated, IsOwner]
    throttle_classes = [LinkAnalyticsThrottle]

    def get(self, request: Request, link_id: str) -> Response:
        link = get_link_by_id(link_id, owner=request.user)
        self.check_object_permissions(request, link)

        try:
            days = int(request.query_params.get("days", 30))
            days = max(1, min(days, 365))
        except (TypeError, ValueError):
            days = 30

        # Redis-cached — subsequent calls within TTL skip the DB aggregation.
        analytics = get_cached_link_analytics(link, days=days)
        return Response(AnalyticsSerializer(analytics).data)
