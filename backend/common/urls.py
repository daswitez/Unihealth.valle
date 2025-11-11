from django.urls import path
from .views import HealthView

urlpatterns = [
    # Ruta base /api/health/
    path('health/', HealthView.as_view(), name='health'),
]

