from typing import Any

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.authentication import get_user_from_request
from .models import PerfilPaciente, Consentimiento
from .serializers import (
    ProfileReadSerializer,
    ProfileWriteSerializer,
    ConsentReadSerializer,
    ConsentCreateSerializer,
)


class MeProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        usuario = get_user_from_request(request)
        if not usuario:
            return Response({"detail": "No autenticado"}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            perfil = PerfilPaciente.objects.get(usuario_id=usuario.id)
        except PerfilPaciente.DoesNotExist:
            return Response({"detail": "Perfil no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        return Response(ProfileReadSerializer(perfil).data, status=status.HTTP_200_OK)

    @transaction.atomic
    def put(self, request):
        usuario = get_user_from_request(request)
        if not usuario:
            return Response({"detail": "No autenticado"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            perfil = PerfilPaciente.objects.get(usuario_id=usuario.id)
            serializer = ProfileWriteSerializer(perfil, data=request.data, partial=False)
        except PerfilPaciente.DoesNotExist:
            serializer = ProfileWriteSerializer(data=request.data, partial=False)

        if not serializer.is_valid():
            return Response({"detail": "Datos inválidos", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        perfil_vals = dict(data)
        perfil_vals["usuario_id"] = usuario.id
        # upsert manual
        PerfilPaciente.objects.update_or_create(usuario_id=usuario.id, defaults=perfil_vals)
        perfil = PerfilPaciente.objects.get(usuario_id=usuario.id)
        return Response(ProfileReadSerializer(perfil).data, status=status.HTTP_200_OK)


class MeConsentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        usuario = get_user_from_request(request)
        if not usuario:
            return Response({"detail": "No autenticado"}, status=status.HTTP_401_UNAUTHORIZED)
        consents = Consentimiento.objects.filter(usuario_id=usuario.id).order_by("-aceptado_en")
        return Response(ConsentReadSerializer(consents, many=True).data, status=status.HTTP_200_OK)

    @transaction.atomic
    def post(self, request):
        usuario = get_user_from_request(request)
        if not usuario:
            return Response({"detail": "No autenticado"}, status=status.HTTP_401_UNAUTHORIZED)

        ser = ConsentCreateSerializer(data=request.data)
        if not ser.is_valid():
            return Response({"detail": "Datos inválidos", "errors": ser.errors}, status=status.HTTP_400_BAD_REQUEST)

        version = ser.validated_data["version"]
        ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip() or request.META.get("REMOTE_ADDR")
        Consentimiento.objects.create(usuario_id=usuario.id, version=version, ip=ip)
        consents = Consentimiento.objects.filter(usuario_id=usuario.id).order_by("-aceptado_en")
        return Response(ConsentReadSerializer(consents, many=True).data, status=status.HTTP_201_CREATED)
from django.shortcuts import render

# Create your views here.
