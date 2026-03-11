from django.urls import path
from apps.links.api.views import LinkAnalyticsView, LinkDetailView, LinkListCreateView

urlpatterns = [
    path("", LinkListCreateView.as_view(), name="links-list-create"),
    path("<str:link_id>/", LinkDetailView.as_view(), name="links-detail"),
    path("<str:link_id>/analytics/", LinkAnalyticsView.as_view(), name="links-analytics"),
]
