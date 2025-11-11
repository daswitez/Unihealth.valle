from datetime import date
from typing import Any, Dict

from rest_framework import serializers

from .models import PerfilPaciente, Consentimiento


class ProfileReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfilPaciente
        fields = [
            "usuario",
            "nombres",
            "apellidos",
            "fecha_nacimiento",
            "sexo",
            "contacto_emergencia",
            "alergias",
            "antecedentes",
            "creado_en",
            "actualizado_en",
        ]
        extra_kwargs = {"usuario": {"read_only": True}}


class ProfileWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfilPaciente
        fields = [
            "nombres",
            "apellidos",
            "fecha_nacimiento",
            "sexo",
            "contacto_emergencia",
            "alergias",
            "antecedentes",
        ]

    def validate_nombres(self, value: str) -> str:
        if not value or not value.strip():
            raise serializers.ValidationError("Nombres es obligatorio.")
        if len(value) > 100:
            raise serializers.ValidationError("Nombres excede el máximo permitido.")
        return value.strip()

    def validate_apellidos(self, value: str) -> str:
        if not value or not value.strip():
            raise serializers.ValidationError("Apellidos es obligatorio.")
        if len(value) > 100:
            raise serializers.ValidationError("Apellidos excede el máximo permitido.")
        return value.strip()

    def validate_fecha_nacimiento(self, value):
        if value and value > date.today():
            raise serializers.ValidationError("La fecha de nacimiento no puede ser futura.")
        return value

    def validate_sexo(self, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        if value not in ("M", "F", "X"):
            raise serializers.ValidationError("Sexo debe ser 'M','F' o 'X'.")
        return value


class ConsentReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consentimiento
        fields = ["id", "version", "aceptado_en", "ip"]


class ConsentCreateSerializer(serializers.Serializer):
    version = serializers.CharField(max_length=20)

