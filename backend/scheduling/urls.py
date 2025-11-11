from django.urls import path

from .views import AppointmentSlotsView, AppointmentsView, AppointmentDetailView

urlpatterns = [
    path("appointments/slots", AppointmentSlotsView.as_view(), name="appointments-slots"),
    path("appointments", AppointmentsView.as_view(), name="appointments"),
    path("appointments/<int:id>", AppointmentDetailView.as_view(), name="appointments-detail"),
]

