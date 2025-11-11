from typing import Any, Dict

from rest_framework import serializers

from accounts.models import Usuario
from .models import TipoNota, RegistroClinico, SignoVital, Adjunto


class TipoNotaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoNota
        fields = ["id", "codigo", "nombre"]


class RecordReadSerializer(serializers.ModelSerializer):
    tipo_nota = TipoNotaSerializer()
    paciente_id = serializers.IntegerField(source="paciente.id")
    creado_por_id = serializers.IntegerField(source="creado_por.id")

    class Meta:
        model = RegistroClinico
        fields = ["id", "paciente_id", "creado_por_id", "tipo_nota", "nota", "creado_en", "actualizado_en"]


class RecordWriteSerializer(serializers.Serializer):
    paciente_id = serializers.IntegerField()
    tipo_nota_codigo = serializers.CharField(max_length=32)
    nota = serializers.CharField(allow_blank=True, required=False)

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        pid = data["paciente_id"]
        code = data["tipo_nota_codigo"]
        if not Usuario.objects.filter(id=pid).exists():
            raise serializers.ValidationError({"paciente_id": "Paciente no existe"})
        tipo = TipoNota.objects.filter(codigo__iexact=code, activo=True).first()
        if not tipo:
            raise serializers.ValidationError({"tipo_nota_codigo": "Tipo de nota inválido"})
        data["_tipo_obj"] = tipo
        return data


class VitalsWriteSerializer(serializers.Serializer):
    paciente_id = serializers.IntegerField()
    pas_sistolica = serializers.IntegerField(required=False, allow_null=True)
    pas_diastolica = serializers.IntegerField(required=False, allow_null=True)
    fcritmo = serializers.IntegerField(required=False, allow_null=True)
    temp_c = serializers.DecimalField(required=False, allow_null=True, max_digits=4, decimal_places=1)
    spo2 = serializers.IntegerField(required=False, allow_null=True)

    def validate_paciente_id(self, value: int) -> int:
        if not Usuario.objects.filter(id=value).exists():
            raise serializers.ValidationError("Paciente no existe")
        return value

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Rango básico para evitar violar constraints BD antes de llegar
        def in_range(val, lo, hi, name):
            if val is None:
                return
            if not (lo <= val <= hi):
                raise serializers.ValidationError({name: f"Fuera de rango permitido [{lo},{hi}]."})

        in_range(data.get("pas_sistolica"), 40, 260, "pas_sistolica")
        in_range(data.get("pas_diastolica"), 20, 160, "pas_diastolica")
        in_range(data.get("fcritmo"), 20, 260, "fcritmo")
        in_range(data.get("spo2"), 50, 100, "spo2")
        t = data.get("temp_c")
        if t is not None and not (30.0 <= float(t) <= 45.0):
            raise serializers.ValidationError({"temp_c": "Fuera de rango permitido [30.0,45.0]."})
        return data


class VitalsReadSerializer(serializers.ModelSerializer):
    paciente_id = serializers.IntegerField(source="paciente.id")
    tomado_por_id = serializers.IntegerField(source="tomado_por.id")

    class Meta:
        model = SignoVital
        fields = ["id", "paciente_id", "tomado_por_id", "pas_sistolica", "pas_diastolica", "fcritmo", "temp_c", "spo2", "tomado_en"]


class AttachmentCreateSerializer(serializers.Serializer):
    propietario_tabla = serializers.ChoiceField(choices=("registros_clinicos", "alertas"))
    propietario_id = serializers.IntegerField()
    file = serializers.FileField()


class AttachmentReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Adjunto
        fields = ["id", "propietario_tabla", "propietario_id", "nombre_archivo", "mime", "ruta_storage", "tamano_bytes", "creado_por_id", "creado_en"]

