import os
import uuid
from typing import Any

from django.conf import settings
from django.db import transaction, connection
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.authentication import get_user_from_request
from accounts.permissions import IsNurse
from .models import RegistroClinico, SignoVital, Adjunto
from .serializers import (
    RecordReadSerializer,
    RecordWriteSerializer,
    VitalsWriteSerializer,
    VitalsReadSerializer,
    AttachmentCreateSerializer,
    AttachmentReadSerializer,
)


class RecordsView(APIView):
    """
    GET /api/records -> usuario: sus registros
    POST /api/records -> enfermería: crea registro
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        usuario = get_user_from_request(request)
        if not usuario:
            return Response({"detail": "No autenticado"}, status=status.HTTP_401_UNAUTHORIZED)
        # Usuario ve sus propios registros
        registros = RegistroClinico.objects.select_related("tipo_nota").filter(paciente_id=usuario.id).order_by("-creado_en")
        return Response(RecordReadSerializer(registros, many=True).data, status=status.HTTP_200_OK)

    @transaction.atomic
    def post(self, request):
        # Solo enfermería
        if not IsNurse().has_permission(request, self):
            return Response({"detail": "Permisos insuficientes"}, status=status.HTTP_403_FORBIDDEN)

        usuario = get_user_from_request(request)
        if not usuario:
            return Response({"detail": "No autenticado"}, status=status.HTTP_401_UNAUTHORIZED)

        ser = RecordWriteSerializer(data=request.data)
        if not ser.is_valid():
            return Response({"detail": "Datos inválidos", "errors": ser.errors}, status=status.HTTP_400_BAD_REQUEST)

        tipo = ser.validated_data["_tipo_obj"]
        rec = RegistroClinico.objects.create(
            paciente_id=ser.validated_data["paciente_id"],
            creado_por_id=usuario.id,
            tipo_nota=tipo,
            nota=ser.validated_data.get("nota", ""),
        )
        rec = RegistroClinico.objects.select_related("tipo_nota").get(id=rec.id)
        return Response(RecordReadSerializer(rec).data, status=status.HTTP_201_CREATED)


class RecordsByPatientView(APIView):
    """
    GET /api/records/<paciente_id> -> enfermería: ver registros del paciente
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, paciente_id: int):
        if not IsNurse().has_permission(request, self):
            return Response({"detail": "Permisos insuficientes"}, status=status.HTTP_403_FORBIDDEN)
        registros = (
            RegistroClinico.objects.select_related("tipo_nota")
            .filter(paciente_id=paciente_id)
            .order_by("-creado_en")
        )
        return Response(RecordReadSerializer(registros, many=True).data, status=status.HTTP_200_OK)


class VitalsCreateView(APIView):
    """
    POST /api/vitals -> enfermería
    """

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        if not IsNurse().has_permission(request, self):
            return Response({"detail": "Permisos insuficientes"}, status=status.HTTP_403_FORBIDDEN)
        usuario = get_user_from_request(request)
        if not usuario:
            return Response({"detail": "No autenticado"}, status=status.HTTP_401_UNAUTHORIZED)

        ser = VitalsWriteSerializer(data=request.data)
        if not ser.is_valid():
            return Response({"detail": "Datos inválidos", "errors": ser.errors}, status=status.HTTP_400_BAD_REQUEST)

        v = SignoVital.objects.create(
            paciente_id=ser.validated_data["paciente_id"],
            tomado_por_id=usuario.id,
            pas_sistolica=ser.validated_data.get("pas_sistolica"),
            pas_diastolica=ser.validated_data.get("pas_diastolica"),
            fcritmo=ser.validated_data.get("fcritmo"),
            temp_c=ser.validated_data.get("temp_c"),
            spo2=ser.validated_data.get("spo2"),
        )
        return Response(VitalsReadSerializer(v).data, status=status.HTTP_201_CREATED)


class VitalsByPatientView(APIView):
    """
    GET /api/vitals/<paciente_id> -> enfermería
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, paciente_id: int):
        if not IsNurse().has_permission(request, self):
            return Response({"detail": "Permisos insuficientes"}, status=status.HTTP_403_FORBIDDEN)
        vs = SignoVital.objects.filter(paciente_id=paciente_id).order_by("-tomado_en")
        return Response(VitalsReadSerializer(vs, many=True).data, status=status.HTTP_200_OK)


class AttachmentCreateView(APIView):
    """
    POST /api/attachments  (multipart/form-data)
    Campos:
      - propietario_tabla: registros_clinicos | alertas
      - propietario_id: id de la fila dueña
      - file: archivo a subir
    """

    permission_classes = [IsAuthenticated, IsNurse]

    @transaction.atomic
    def post(self, request):
        ser = AttachmentCreateSerializer(data=request.data)
        if not ser.is_valid():
            return Response({"detail": "Datos inválidos", "errors": ser.errors}, status=status.HTTP_400_BAD_REQUEST)

        propietario_tabla = ser.validated_data["propietario_tabla"]
        propietario_id = ser.validated_data["propietario_id"]
        upfile = request.FILES.get("file")
        if not upfile:
            return Response({"detail": "Falta archivo 'file'."}, status=status.HTTP_400_BAD_REQUEST)

        # Validar que exista el owner (usando SQL directo para evitar dependencias cruzadas)
        with connection.cursor() as cur:
            cur.execute(f'SELECT 1 FROM app."{propietario_tabla}" WHERE id=%s', [propietario_id])
            if cur.fetchone() is None:
                return Response({"detail": "Propietario no existe"}, status=status.HTTP_400_BAD_REQUEST)

        # Guardar archivo en MEDIA/attachments
        attach_dir = os.path.join(settings.MEDIA_ROOT, "attachments")
        os.makedirs(attach_dir, exist_ok=True)
        filename = f"{uuid.uuid4().hex}_{upfile.name}"
        storage_path = os.path.join(attach_dir, filename)
        with open(storage_path, "wb") as dest:
            for chunk in upfile.chunks():
                dest.write(chunk)
        rel_path = f"/media/attachments/{filename}"

        adj = Adjunto.objects.create(
            propietario_tabla=propietario_tabla,
            propietario_id=propietario_id,
            nombre_archivo=upfile.name,
            mime=upfile.content_type or "application/octet-stream",
            ruta_storage=rel_path,
            tamano_bytes=upfile.size,
            creado_por_id=get_user_from_request(request).id,
        )
        return Response(AttachmentReadSerializer(adj).data, status=status.HTTP_201_CREATED)


class AttachmentsListView(APIView):
    """
    GET /api/attachments?propietario_tabla=registros_clinicos&propietario_id=123  (enfermería)
    Lista adjuntos de un propietario concreto.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not IsNurse().has_permission(request, self):
            return Response({"detail": "Permisos insuficientes"}, status=status.HTTP_403_FORBIDDEN)
        owner_table = request.query_params.get("propietario_tabla")
        owner_id = request.query_params.get("propietario_id")
        if not owner_table or not owner_id:
            return Response({"detail": "Faltan propietario_tabla y propietario_id"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            owner_id_int = int(owner_id)
        except ValueError:
            return Response({"detail": "propietario_id inválido"}, status=status.HTTP_400_BAD_REQUEST)
        qs = Adjunto.objects.filter(propietario_tabla=owner_table, propietario_id=owner_id_int).order_by("-creado_en")
        return Response(AttachmentReadSerializer(qs, many=True).data, status=status.HTTP_200_OK)


class AttachmentDetailView(APIView):
    """
    GET /api/attachments/<id>  (enfermería)
    Devuelve metadatos del adjunto (la ruta pública está en ruta_storage).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, id: int):
        if not IsNurse().has_permission(request, self):
            return Response({"detail": "Permisos insuficientes"}, status=status.HTTP_403_FORBIDDEN)
        try:
            adj = Adjunto.objects.get(id=id)
        except Adjunto.DoesNotExist:
            return Response({"detail": "Adjunto no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        return Response(AttachmentReadSerializer(adj).data, status=status.HTTP_200_OK)
from django.shortcuts import render

# Create your views here.
