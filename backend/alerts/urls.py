from django.urls import path

from .views import AlertsView, AlertDetailView, AlertAssignView, AlertStatusView, AlertEventView

urlpatterns = [
    path("alerts", AlertsView.as_view(), name="alerts"),
    path("alerts/<int:id>", AlertDetailView.as_view(), name="alert-detail"),
    path("alerts/<int:id>/assign", AlertAssignView.as_view(), name="alert-assign"),
    path("alerts/<int:id>/status", AlertStatusView.as_view(), name="alert-status"),
    path("alerts/<int:id>/event", AlertEventView.as_view(), name="alert-event"),
]

