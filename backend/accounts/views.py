from typing import Any, Dict

from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .authentication import get_user_from_request
from .jwt_utils import create_access_token, create_refresh_token, decode_token
from .serializers import LoginSerializer, MeSerializer, RegisterSerializer, authenticate_user
from django.db import transaction
from django.contrib.auth.hashers import make_password
from .models import Usuario, Role


class LoginView(APIView):
    """
    POST /api/auth/login
    Autentica por email+password, devuelve access y refresh tokens y datos del usuario.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"detail": "Datos inválidos", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        auth = authenticate_user(email, password)
        if not auth.ok or not auth.user:
            return Response({"detail": auth.error or "Credenciales inválidas"}, status=status.HTTP_401_UNAUTHORIZED)

        user = auth.user
        # Marcar último login (omitir silenciosamente si el objeto es un mock u otro tipo no administrado)
        try:
            type(user).objects.filter(id=user.id).update(ultimo_login=timezone.now())
        except Exception:
            pass

        base_claims: Dict[str, Any] = {"sub": user.id, "email": user.email, "role": user.rol.nombre}
        access = create_access_token(base_claims)
        refresh = create_refresh_token(base_claims)

        user_data = {
            "id": user.id,
            "email": user.email,
            "rol": user.rol.nombre,
            "activo": True,
        }
        data = {
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "Bearer",
            "user": user_data,
        }
        return Response(data, status=status.HTTP_200_OK)


class RefreshView(APIView):
    """
    POST /api/auth/refresh
    Recibe refresh token y emite un nuevo access token.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get("refresh_token")
        if not token:
            return Response({"detail": "Falta refresh_token"}, status=status.HTTP_400_BAD_REQUEST)

        claims = decode_token(token)
        if not claims or claims.get("type") != "refresh":
            return Response({"detail": "Refresh token inválido o expirado"}, status=status.HTTP_401_UNAUTHORIZED)

        new_access = create_access_token({"sub": claims.get("sub"), "email": claims.get("email"), "role": claims.get("role")})
        return Response({"access_token": new_access, "token_type": "Bearer"}, status=status.HTTP_200_OK)


class MeView(APIView):
    """
    GET /api/auth/me
    Devuelve información del usuario autenticado.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        usuario = get_user_from_request(request)
        if not usuario:
            return Response({"detail": "No autenticado"}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(MeSerializer(usuario).data, status=status.HTTP_200_OK)


class RegisterView(APIView):
    """
    POST /api/auth/register
    Crea un usuario en app.usuarios con rol (por defecto 'user'), y devuelve tokens.
    """

    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"detail": "Datos inválidos", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]
        role_name = serializer.validated_data.get("role", "user")

        try:
            rol = Role.objects.get(nombre=role_name)
        except Role.DoesNotExist:
            return Response({"detail": "Rol no encontrado"}, status=status.HTTP_400_BAD_REQUEST)

        user = Usuario.objects.create(
            email=email,
            pass_hash=make_password(password),
            rol=rol,
            activo=True,
        )

        claims: Dict[str, Any] = {"sub": user.id, "email": user.email, "role": user.rol.nombre}
        access = create_access_token(claims)
        refresh = create_refresh_token(claims)

        return Response(
            {
                "access_token": access,
                "refresh_token": refresh,
                "token_type": "Bearer",
                "user": {"id": user.id, "email": user.email, "rol": user.rol.nombre, "activo": True},
            },
            status=status.HTTP_201_CREATED,
        )
from django.shortcuts import render

# Create your views here.
