from dataclasses import dataclass
from typing import Any, Dict

from django.contrib.auth.hashers import check_password, identify_hasher
from rest_framework import serializers

from .models import Usuario, Role


@dataclass
class AuthResult:
    ok: bool
    user: Usuario | None = None
    error: str | None = None


def check_passhash(stored_hash: str, raw_password: str) -> bool:
    """
    Comprueba la contraseña comparando contra un hash estilo Django.
    Si el hash no es reconocible por Django, retorna False.
    """
    try:
        identify_hasher(stored_hash)  # valida formato
    except Exception:
        return False
    return check_password(raw_password, stored_hash)


def authenticate_user(email: str, password: str) -> AuthResult:
    """
    Autenticación contra app.usuarios usando pass_hash. Requiere que el hash sea compatible con Django.
    """
    try:
        usuario = Usuario.objects.select_related("rol").get(email=email)
    except Usuario.DoesNotExist:
        return AuthResult(ok=False, error="Credenciales inválidas")

    if not usuario.activo:
        return AuthResult(ok=False, error="Usuario inactivo")

    if not check_passhash(usuario.pass_hash, password):
        return AuthResult(ok=False, error="Credenciales inválidas")

    return AuthResult(ok=True, user=usuario)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class MeSerializer(serializers.ModelSerializer):
    rol = serializers.CharField(source="rol.nombre")

    class Meta:
        model = Usuario
        fields = ["id", "email", "rol", "activo", "creado_en", "actualizado_en", "ultimo_login"]


class RegisterSerializer(serializers.Serializer):
    """
    Serializer de registro mínimo. Por defecto asigna rol 'user' si no se indica otro.
    """

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8, trim_whitespace=False)
    role = serializers.CharField(required=False, allow_blank=True)

    def validate_email(self, value: str) -> str:
        if Usuario.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email ya registrado")
        return value

    def validate_role(self, value: str) -> str:
        if not value:
            return "user"
        nombre = value.strip().lower()
        if not Role.objects.filter(nombre=nombre).exists():
            raise serializers.ValidationError("Rol inválido")
        return nombre

