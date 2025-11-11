from django.urls import path

from .views import (
    RecordsView,
    RecordsByPatientView,
    VitalsCreateView,
    VitalsByPatientView,
    AttachmentCreateView,
    AttachmentsListView,
    AttachmentDetailView,
)

urlpatterns = [
    path("records", RecordsView.as_view(), name="records"),
    path("records/<int:paciente_id>", RecordsByPatientView.as_view(), name="records-by-patient"),
    path("vitals", VitalsCreateView.as_view(), name="vitals-create"),
    path("vitals/<int:paciente_id>", VitalsByPatientView.as_view(), name="vitals-by-patient"),
    path("attachments", AttachmentCreateView.as_view(), name="attachments-create"),
    path("attachments", AttachmentsListView.as_view(), name="attachments-list"),
    path("attachments/<int:id>", AttachmentDetailView.as_view(), name="attachments-detail"),
]

