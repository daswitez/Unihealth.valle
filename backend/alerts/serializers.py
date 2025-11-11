from typing import Any, Dict

from rest_framework import serializers

from accounts.models import Usuario
from .models import TipoAlerta, Alerta, EventoAlerta


class TipoAlertaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoAlerta
        fields = ["id", "codigo", "nombre"]


class AlertaReadSerializer(serializers.ModelSerializer):
    tipo_alerta = TipoAlertaSerializer()
    paciente_id = serializers.IntegerField(source="paciente.id", allow_null=True)
    asignado_a_id = serializers.IntegerField(source="asignado_a.id", allow_null=True)

    class Meta:
        model = Alerta
        fields = [
            "id",
            "paciente_id",
            "tipo_alerta",
            "estado",
            "latitud",
            "longitud",
            "descripcion",
            "creado_en",
            "asignado_a_id",
            "resuelto_en",
            "fuente",
        ]


class AlertaCreateSerializer(serializers.Serializer):
    latitud = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    longitud = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    descripcion = serializers.CharField(required=False, allow_blank=True)
    tipo_alerta_codigo = serializers.CharField(required=False, allow_blank=True)
    fuente = serializers.ChoiceField(choices=("app", "kiosco", "admin"), default="app")

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        code = data.get("tipo_alerta_codigo", "")
        if code:
            tipo = TipoAlerta.objects.filter(codigo__iexact=code, activo=True).first()
            if not tipo:
                raise serializers.ValidationError({"tipo_alerta_codigo": "Tipo de alerta inválido"})
            data["_tipo_obj"] = tipo
        return data


class AlertaAssignSerializer(serializers.Serializer):
    asignado_a_id = serializers.IntegerField(required=False)


class AlertaStatusSerializer(serializers.Serializer):
    estado = serializers.ChoiceField(choices=("en_curso", "resuelta"))


class AlertaEventSerializer(serializers.Serializer):
    tipo = serializers.ChoiceField(choices=("nota", "adjunto", "cambio_estado"))
    detalle_json = serializers.JSONField(required=False)

