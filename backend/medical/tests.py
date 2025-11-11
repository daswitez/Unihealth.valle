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
  nombre VARCHAR(32) NOT NULL UNIQUE,
  descripcion TEXT
);

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

CREATE TABLE IF NOT EXISTS app.tipos_nota (
  id BIGSERIAL PRIMARY KEY,
  codigo VARCHAR(32) NOT NULL UNIQUE,
  nombre VARCHAR(80) NOT NULL,
  activo BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS app.registros_clinicos (
  id BIGSERIAL PRIMARY KEY,
  paciente_id BIGINT NOT NULL REFERENCES app.usuarios(id) ON DELETE CASCADE,
  creado_por_id BIGINT NOT NULL REFERENCES app.usuarios(id),
  tipo_nota_id BIGINT NOT NULL REFERENCES app.tipos_nota(id),
  nota TEXT,
  creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  actualizado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS app.signos_vitales (
  id BIGSERIAL PRIMARY KEY,
  paciente_id BIGINT NOT NULL REFERENCES app.usuarios(id) ON DELETE CASCADE,
  tomado_por_id BIGINT NOT NULL REFERENCES app.usuarios(id),
  pas_sistolica SMALLINT,
  pas_diastolica SMALLINT,
  fcritmo SMALLINT,
  temp_c NUMERIC(4,1),
  spo2 SMALLINT,
  tomado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO app.roles (nombre) VALUES ('user'),('nurse') ON CONFLICT (nombre) DO NOTHING;
INSERT INTO app.tipos_nota (codigo, nombre, activo) VALUES ('triaje','Nota de triaje', TRUE)
ON CONFLICT (codigo) DO NOTHING;
"""


class MedicalEndpointsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with connection.cursor() as cursor:
            cursor.execute(DDL)
        from accounts.models import Usuario, Role
        nurse_role = Role.objects.get(nombre="nurse")
        user_role = Role.objects.get(nombre="user")
        cls.nurse = Usuario.objects.create(
            email="nurse@example.com", pass_hash=make_password("Secret123!"), rol=nurse_role, activo=True
        )
        cls.patient = Usuario.objects.create(
            email="patient2@example.com", pass_hash=make_password("Secret123!"), rol=user_role, activo=True
        )
        cls.nurse_access = create_access_token({"sub": str(cls.nurse.id), "email": cls.nurse.email, "role": "nurse"}, 600)

    def setUp(self):
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.nurse_access}")

    def test_create_record_and_vitals(self):
        # Crear registro clínico
        res = self.client.post(
            reverse("records"),
            {"paciente_id": self.patient.id, "tipo_nota_codigo": "triaje", "nota": "Paciente estable"},
            format="json",
        )
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data["tipo_nota"]["codigo"], "triaje")

        # Crear signos vitales
        res = self.client.post(
            reverse("vitals-create"),
            {"paciente_id": self.patient.id, "pas_sistolica": 120, "pas_diastolica": 80, "spo2": 98},
            format="json",
        )
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data["paciente_id"], self.patient.id)

        # Listar registros por paciente (enfermería)
        res = self.client.get(reverse("records-by-patient", args=[self.patient.id]))
        self.assertEqual(res.status_code, 200)
        self.assertTrue(len(res.data) >= 1)

        # Listar signos vitales por paciente
        res = self.client.get(reverse("vitals-by-patient", args=[self.patient.id]))
        self.assertEqual(res.status_code, 200)
        self.assertTrue(len(res.data) >= 1)
from django.test import TestCase

# Create your tests here.
