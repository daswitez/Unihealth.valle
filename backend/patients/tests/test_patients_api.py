from django.test import TestCase
from django.urls import reverse
from django.db import connection
from rest_framework.test import APIClient
from django.contrib.auth.hashers import make_password

from accounts.jwt_utils import create_access_token


DDL = """
CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS app.roles (
  id BIGSERIAL PRIMARY KEY,
  nombre VARCHAR(32) NOT NULL UNIQUE
);
ALTER TABLE app.roles ADD COLUMN IF NOT EXISTS descripcion TEXT;

CREATE TABLE IF NOT EXISTS app.usuarios (
  id BIGSERIAL PRIMARY KEY,
  email VARCHAR(254) NOT NULL UNIQUE,
  pass_hash TEXT NOT NULL,
  rol_id BIGINT NOT NULL REFERENCES app.roles(id),
  activo BOOLEAN NOT NULL DEFAULT TRUE,
  creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  actualizado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  ultimo_login TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS app.perfiles_paciente (
  usuario_id BIGINT PRIMARY KEY REFERENCES app.usuarios(id) ON DELETE CASCADE,
  nombres VARCHAR(100) NOT NULL,
  apellidos VARCHAR(100) NOT NULL,
  fecha_nacimiento DATE,
  sexo CHAR(1),
  contacto_emergencia VARCHAR(100),
  alergias TEXT,
  antecedentes TEXT,
  creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  actualizado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS app.consentimientos (
  id BIGSERIAL PRIMARY KEY,
  usuario_id BIGINT NOT NULL REFERENCES app.usuarios(id) ON DELETE CASCADE,
  version VARCHAR(20) NOT NULL,
  aceptado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  ip INET
);

INSERT INTO app.roles (nombre) VALUES ('user') ON CONFLICT (nombre) DO NOTHING;
"""


class PatientsEndpointsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with connection.cursor() as cursor:
            cursor.execute(DDL)
        # Crear usuario de prueba
        from accounts.models import Usuario, Role
        role = Role.objects.get(nombre="user")
        cls.user = Usuario.objects.create(
            email="patient@example.com",
            pass_hash=make_password("Secret123!"),
            rol=role,
            activo=True,
        )
        claims = {"sub": str(cls.user.id), "email": cls.user.email, "role": "user"}
        cls.access = create_access_token(claims, expires_in_seconds=600)

    def setUp(self):
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access}")

    def test_profile_crud(self):
        # GET antes de crear -> 404
        url = reverse("me-profile")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 404)

        # PUT crear perfil
        payload = {
            "nombres": "Paciente",
            "apellidos": "Demo",
            "fecha_nacimiento": "2000-01-01",
            "sexo": "X",
            "contacto_emergencia": "Contacto",
            "alergias": "Ninguna",
            "antecedentes": "N/A",
        }
        res = self.client.put(url, payload, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["nombres"], "Paciente")

        # GET ahora -> 200
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["apellidos"], "Demo")

    def test_consents_flow(self):
        url = reverse("me-consents")
        # LIST vacío
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, [])

        # CREATE
        res = self.client.post(url, {"version": "v1.0"}, format="json")
        self.assertEqual(res.status_code, 201)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["version"], "v1.0")

