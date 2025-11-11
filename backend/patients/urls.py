from django.urls import path

from .views import MeProfileView, MeConsentsView

urlpatterns = [
    path("me/profile", MeProfileView.as_view(), name="me-profile"),
    path("me/consentimientos", MeConsentsView.as_view(), name="me-consents"),
]

