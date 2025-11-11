from typing import Optional, Tuple

from django.contrib.auth.models import AnonymousUser
from rest_framework import authentication, exceptions

from .jwt_utils import decode_token
from .models import Usuario


class SimpleUser:
    """
    Representa un usuario autenticado para DRF sin depender de django.contrib.auth.User.
    """

    def __init__(self, user_id: int, email: str, role_name: str) -> None:
        self.id = user_id
        self.email = email
        self.role = role_name
        self.is_authenticated = True

    def __str__(self) -> str:
        return f"{self.email} ({self.role})"


class JwtAuthentication(authentication.BaseAuthentication):
    """
    Autenticación vía JWT en header Authorization: Bearer <token>.
    """

    keyword = "Bearer"

    def authenticate(self, request) -> Optional[Tuple[SimpleUser, None]]:
        auth_header = authentication.get_authorization_header(request).decode("utf-8")
        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0] != self.keyword:
            raise exceptions.AuthenticationFailed("Formato de Authorization inválido")

        claims = decode_token(parts[1])
        if not claims or claims.get("type") != "access":
            raise exceptions.AuthenticationFailed("Token inválido o expirado")

        user_id = claims.get("sub")
        email = claims.get("email")
        role = claims.get("role")
        if not user_id or not email or not role:
            raise exceptions.AuthenticationFailed("Token sin claims requeridos")

        # Verificar que el usuario exista y esté activo
        try:
            usuario = Usuario.objects.only("id", "email", "activo", "rol__nombre").select_related("rol").get(id=user_id, email=email)
        except Usuario.DoesNotExist:
            raise exceptions.AuthenticationFailed("Usuario no encontrado")

        if not usuario.activo:
            raise exceptions.AuthenticationFailed("Usuario inactivo")

        return SimpleUser(usuario.id, usuario.email, usuario.rol.nombre), None


def get_user_from_request(request):
    """
    Helper para obtener un objeto Usuario desde request (cargando de BD si es necesario).
    """
    user = getattr(request, "user", None)
    if not user or isinstance(user, AnonymousUser):
        return None
    try:
        return Usuario.objects.select_related("rol").get(id=user.id)
    except Usuario.DoesNotExist:
        return None

