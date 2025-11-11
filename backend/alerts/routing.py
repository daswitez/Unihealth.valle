from django.urls import re_path

from .consumers import AlertsConsumer

websocket_urlpatterns = [
    re_path(r"^ws/alerts$", AlertsConsumer.as_asgi()),
]

