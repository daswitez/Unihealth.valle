from datetime import datetime, timedelta, time, date
from typing import Any, Dict, List

from django.utils import timezone
from rest_framework import serializers

from accounts.models import Usuario
from .models import Cita, Agenda, TipoServicio


DEFAULT_SLOT_MINUTES = 30


class SlotsQuerySerializer(serializers.Serializer):
    enfermero_id = serializers.IntegerField()
    date = serializers.DateField()
    slot_minutes = serializers.IntegerField(required=False, min_value=5, max_value=240)

    def validate_enfermero_id(self, value: int) -> int:
        if not Usuario.objects.filter(id=value).exists():
            raise serializers.ValidationError("Enfermero no existe")
        return value


class AppointmentCreateSerializer(serializers.Serializer):
    paciente_id = serializers.IntegerField()
    enfermero_id = serializers.IntegerField()
    tipo_servicio_codigo = serializers.CharField(max_length=32)
    start_ts = serializers.DateTimeField()
    end_ts = serializers.DateTimeField()
    reason = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # paciente y enfermero deben existir
        if not Usuario.objects.filter(id=data["paciente_id"]).exists():
            raise serializers.ValidationError({"paciente_id": "Paciente no existe"})
        if not Usuario.objects.filter(id=data["enfermero_id"]).exists():
            raise serializers.ValidationError({"enfermero_id": "Enfermero no existe"})
        # tipo servicio
        ts = TipoServicio.objects.filter(codigo__iexact=data["tipo_servicio_codigo"], activo=True).first()
        if not ts:
            raise serializers.ValidationError({"tipo_servicio_codigo": "Tipo de servicio inválido"})
        data["_tipo_servicio"] = ts
        # rango horario coherente
        if data["end_ts"] <= data["start_ts"]:
            raise serializers.ValidationError({"end_ts": "Debe ser mayor que start_ts"})
        return data


class AppointmentReadSerializer(serializers.ModelSerializer):
    paciente_id = serializers.IntegerField(source="paciente.id")
    enfermero_id = serializers.IntegerField(source="enfermero.id")
    tipo_servicio_codigo = serializers.CharField(source="tipo_servicio.codigo")

    class Meta:
        model = Cita
        fields = ["id", "paciente_id", "enfermero_id", "tipo_servicio_codigo", "inicio", "fin", "estado", "motivo", "creado_en"]


class AppointmentPatchSerializer(serializers.Serializer):
    estado = serializers.ChoiceField(choices=("confirmada", "cancelada", "inasistencia", "atendida"))

