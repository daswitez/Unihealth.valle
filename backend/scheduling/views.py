from datetime import datetime, timedelta
from typing import List, Tuple

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.authentication import get_user_from_request
from accounts.permissions import IsNurse
from .models import Agenda, Cita
from .serializers import (
    SlotsQuerySerializer,
    AppointmentCreateSerializer,
    AppointmentReadSerializer,
    AppointmentPatchSerializer,
    DEFAULT_SLOT_MINUTES,
)


def _overlaps(a_start, a_end, b_start, b_end) -> bool:
    return not (a_end <= b_start or a_start >= b_end)


def _generate_slots_for_day(enfermero_id: int, day: datetime, slot_minutes: int) -> List[Tuple[datetime, datetime]]:
    weekday = day.weekday()  # Monday=0
    blocks = Agenda.objects.filter(enfermero_id=enfermero_id, dia_semana=weekday)
    slots: List[Tuple[datetime, datetime]] = []
    for b in blocks:
        block_start = timezone.make_aware(datetime.combine(day.date(), b.hora_inicio)) if timezone.is_naive(day) else datetime.combine(day.date(), b.hora_inicio).astimezone(timezone.utc)
        block_end = timezone.make_aware(datetime.combine(day.date(), b.hora_fin)) if timezone.is_naive(day) else datetime.combine(day.date(), b.hora_fin).astimezone(timezone.utc)
        cur = block_start
        while cur + timedelta(minutes=slot_minutes) <= block_end:
            slots.append((cur, cur + timedelta(minutes=slot_minutes)))
            cur = cur + timedelta(minutes=slot_minutes)
    # quitar las que colisionan con citas existentes (no canceladas)
    appts = Cita.objects.filter(enfermero_id=enfermero_id, inicio__date=day.date()).exclude(estado="cancelada")
    filtered: List[Tuple[datetime, datetime]] = []
    for s in slots:
        if any(_overlaps(s[0], s[1], a.inicio, a.fin) for a in appts):
            continue
        filtered.append(s)
    return filtered


class AppointmentSlotsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ser = SlotsQuerySerializer(data=request.query_params)
        if not ser.is_valid():
            return Response({"detail": "Parámetros inválidos", "errors": ser.errors}, status=status.HTTP_400_BAD_REQUEST)
        enfermero_id = ser.validated_data["enfermero_id"]
        day = ser.validated_data["date"]
        slot_minutes = ser.validated_data.get("slot_minutes") or DEFAULT_SLOT_MINUTES
        day_dt = timezone.make_aware(datetime.combine(day, datetime.min.time()))
        slots = _generate_slots_for_day(enfermero_id, day_dt, slot_minutes)
        return Response([{"start": s[0], "end": s[1]} for s in slots], status=status.HTTP_200_OK)


class AppointmentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = get_user_from_request(request)
        if not user:
            return Response({"detail": "No autenticado"}, status=status.HTTP_401_UNAUTHORIZED)
        mine = request.query_params.get("mine") == "true"
        qs = Cita.objects.all().order_by("-inicio")
        if mine:
            if user.rol.nombre == "nurse":
                qs = qs.filter(enfermero_id=user.id)
            else:
                qs = qs.filter(paciente_id=user.id)
        return Response(AppointmentReadSerializer(qs, many=True).data, status=status.HTTP_200_OK)

    @transaction.atomic
    def post(self, request):
        user = get_user_from_request(request)
        if not user:
            return Response({"detail": "No autenticado"}, status=status.HTTP_401_UNAUTHORIZED)
        ser = AppointmentCreateSerializer(data=request.data)
        if not ser.is_valid():
            return Response({"detail": "Datos inválidos", "errors": ser.errors}, status=status.HTTP_400_BAD_REQUEST)
        # Permisos: user solo puede crear para sí mismo
        if user.rol.nombre != "nurse" and ser.validated_data["paciente_id"] != user.id:
            return Response({"detail": "No autorizado para crear citas para otros"}, status=status.HTTP_403_FORBIDDEN)
        start = ser.validated_data["start_ts"]
        end = ser.validated_data["end_ts"]
        enfermero_id = ser.validated_data["enfermero_id"]
        # Validar solapamiento
        conflicts = Cita.objects.filter(enfermero_id=enfermero_id).exclude(estado="cancelada").filter(inicio__lt=end, fin__gt=start).exists()
        if conflicts:
            return Response({"detail": "Conflicto: el horario se solapa con otra cita"}, status=status.HTTP_409_CONFLICT)
        # Crear
        status_init = "confirmada" if user.rol.nombre == "nurse" else "solicitada"
        appt = Cita.objects.create(
            paciente_id=ser.validated_data["paciente_id"],
            enfermero_id=enfermero_id,
            tipo_servicio=ser.validated_data["_tipo_servicio"],
            inicio=start,
            fin=end,
            estado=status_init,
            motivo=ser.validated_data.get("reason", ""),
        )
        return Response(AppointmentReadSerializer(appt).data, status=status.HTTP_201_CREATED)


class AppointmentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def patch(self, request, id: int):
        user = get_user_from_request(request)
        try:
            appt = Cita.objects.get(id=id)
        except Cita.DoesNotExist:
            return Response({"detail": "Cita no encontrada"}, status=status.HTTP_404_NOT_FOUND)
        ser = AppointmentPatchSerializer(data=request.data)
        if not ser.is_valid():
            return Response({"detail": "Datos inválidos", "errors": ser.errors}, status=status.HTTP_400_BAD_REQUEST)
        new_state = ser.validated_data["estado"]
        # Permisos: nurse puede cambiar a cualquier estado; user solo puede cancelar su propia
        if user.rol.nombre != "nurse":
            if new_state != "cancelada" or appt.paciente_id != user.id:
                return Response({"detail": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)
        appt.estado = new_state
        appt.save(update_fields=["estado"])
        return Response(AppointmentReadSerializer(appt).data, status=status.HTTP_200_OK)
from django.shortcuts import render

# Create your views here.
