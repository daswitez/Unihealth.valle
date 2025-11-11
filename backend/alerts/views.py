from typing import Any

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.authentication import get_user_from_request
from accounts.permissions import IsNurse
from .models import Alerta, TipoAlerta, EventoAlerta
from .serializers import (
    AlertaReadSerializer,
    AlertaCreateSerializer,
    AlertaAssignSerializer,
    AlertaStatusSerializer,
    AlertaEventSerializer,
)


def _emit_alert_event(event_type: str, payload: dict) -> None:
    """
    Emite eventos por el canal de WebSocket 'alerts'.
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "alerts",
        {
            "type": "alerts.message",
            "event": event_type,
            "payload": payload,
        },
    )


class AlertsView(APIView):
    """
    POST /api/alerts  -> usuario crea alerta (estado=pendiente)
    GET /api/alerts   -> usuario ve propias, enfermería ve todas
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = get_user_from_request(request)
        if not user:
            return Response({"detail": "No autenticado"}, status=status.HTTP_401_UNAUTHORIZED)
        if user.rol.nombre == "nurse":
            qs = Alerta.objects.select_related("tipo_alerta").order_by("-creado_en")
        else:
            qs = Alerta.objects.select_related("tipo_alerta").filter(paciente_id=user.id).order_by("-creado_en")
        return Response(AlertaReadSerializer(qs, many=True).data, status=status.HTTP_200_OK)

    @transaction.atomic
    def post(self, request):
        user = get_user_from_request(request)
        if not user:
            return Response({"detail": "No autenticado"}, status=status.HTTP_401_UNAUTHORIZED)
        # Cualquier usuario autenticado puede crear (source app/kiosco)
        ser = AlertaCreateSerializer(data=request.data)
        if not ser.is_valid():
            return Response({"detail": "Datos inválidos", "errors": ser.errors}, status=status.HTTP_400_BAD_REQUEST)

        tipo = ser.validated_data.get("_tipo_obj")
        alert = Alerta.objects.create(
            paciente_id=user.id,
            tipo_alerta=tipo,
            estado="pendiente",
            latitud=ser.validated_data.get("latitud"),
            longitud=ser.validated_data.get("longitud"),
            descripcion=ser.validated_data.get("descripcion", ""),
            fuente=ser.validated_data.get("fuente", "app"),
        )
        EventoAlerta.objects.create(alerta=alert, por_usuario_id=user.id, tipo="creada", detalle_json={})
        _emit_alert_event("alert_created", {"id": alert.id})
        return Response(AlertaReadSerializer(alert).data, status=status.HTTP_201_CREATED)


class AlertDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id: int):
        user = get_user_from_request(request)
        try:
            alert = Alerta.objects.select_related("tipo_alerta").get(id=id)
        except Alerta.DoesNotExist:
            return Response({"detail": "No encontrada"}, status=status.HTTP_404_NOT_FOUND)
        if user.rol.nombre != "nurse" and alert.paciente_id != user.id:
            return Response({"detail": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)
        return Response(AlertaReadSerializer(alert).data, status=status.HTTP_200_OK)


class AlertAssignView(APIView):
    """
    POST /api/alerts/:id/assign -> enfermería asigna (por defecto a sí mismo)
    """

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, id: int):
        if not IsNurse().has_permission(request, self):
            return Response({"detail": "Permisos insuficientes"}, status=status.HTTP_403_FORBIDDEN)
        nurse = get_user_from_request(request)
        try:
            alert = Alerta.objects.get(id=id)
        except Alerta.DoesNotExist:
            return Response({"detail": "No encontrada"}, status=status.HTTP_404_NOT_FOUND)

        ser = AlertaAssignSerializer(data=request.data)
        ser.is_valid(raise_exception=False)
        asignado_id = ser.validated_data.get("asignado_a_id", nurse.id) if ser.validated_data else nurse.id

        alert.asignado_a_id = asignado_id
        if alert.estado == "pendiente":
            alert.estado = "en_curso"
        alert.save(update_fields=["asignado_a_id", "estado"])

        EventoAlerta.objects.create(alerta=alert, por_usuario_id=nurse.id, tipo="asignada", detalle_json={"asignado_a_id": asignado_id})
        EventoAlerta.objects.create(alerta=alert, por_usuario_id=nurse.id, tipo="cambio_estado", detalle_json={"estado": alert.estado})
        _emit_alert_event("alert_assigned", {"id": alert.id, "asignado_a_id": asignado_id})
        return Response(AlertaReadSerializer(alert).data, status=status.HTTP_200_OK)


class AlertStatusView(APIView):
    """
    POST /api/alerts/:id/status -> enfermería cambia estado (en_curso | resuelta)
    """

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, id: int):
        if not IsNurse().has_permission(request, self):
            return Response({"detail": "Permisos insuficientes"}, status=status.HTTP_403_FORBIDDEN)
        nurse = get_user_from_request(request)
        try:
            alert = Alerta.objects.get(id=id)
        except Alerta.DoesNotExist:
            return Response({"detail": "No encontrada"}, status=status.HTTP_404_NOT_FOUND)

        ser = AlertaStatusSerializer(data=request.data)
        if not ser.is_valid():
            return Response({"detail": "Datos inválidos", "errors": ser.errors}, status=status.HTTP_400_BAD_REQUEST)

        new_state = ser.validated_data["estado"]
        if new_state == alert.estado:
            return Response(AlertaReadSerializer(alert).data, status=status.HTTP_200_OK)

        alert.estado = new_state
        if new_state == "resuelta":
            from django.utils import timezone
            alert.resuelto_en = timezone.now()
        alert.save(update_fields=["estado", "resuelto_en"])

        EventoAlerta.objects.create(alerta=alert, por_usuario_id=nurse.id, tipo="cambio_estado", detalle_json={"estado": new_state})
        _emit_alert_event("alert_status", {"id": alert.id, "estado": new_state})
        return Response(AlertaReadSerializer(alert).data, status=status.HTTP_200_OK)


class AlertEventView(APIView):
    """
    POST /api/alerts/:id/event -> añade evento libre (nota/adjunto) por enfermería
    """

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, id: int):
        if not IsNurse().has_permission(request, self):
            return Response({"detail": "Permisos insuficientes"}, status=status.HTTP_403_FORBIDDEN)
        nurse = get_user_from_request(request)
        try:
            alert = Alerta.objects.get(id=id)
        except Alerta.DoesNotExist:
            return Response({"detail": "No encontrada"}, status=status.HTTP_404_NOT_FOUND)

        ser = AlertaEventSerializer(data=request.data)
        if not ser.is_valid():
            return Response({"detail": "Datos inválidos", "errors": ser.errors}, status=status.HTTP_400_BAD_REQUEST)

        ev = EventoAlerta.objects.create(
            alerta=alert, por_usuario_id=nurse.id, tipo=ser.validated_data["tipo"], detalle_json=ser.validated_data.get("detalle_json", {})
        )
        _emit_alert_event("alert_event", {"id": alert.id, "event_id": ev.id, "tipo": ev.tipo})
        return Response({"ok": True, "event_id": ev.id}, status=status.HTTP_201_CREATED)
from django.shortcuts import render

# Create your views here.
