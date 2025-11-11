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

CREATE TABLE IF NOT EXISTS app.tipos_alerta (
  id BIGSERIAL PRIMARY KEY,
  codigo VARCHAR(32) NOT NULL UNIQUE,
  nombre VARCHAR(80) NOT NULL,
  activo BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS app.alertas (
  id BIGSERIAL PRIMARY KEY,
  paciente_id BIGINT REFERENCES app.usuarios(id) ON DELETE SET NULL,
  tipo_alerta_id BIGINT REFERENCES app.tipos_alerta(id),
  estado VARCHAR(20) NOT NULL DEFAULT 'pendiente',
  latitud NUMERIC(9,6),
  longitud NUMERIC(9,6),
  descripcion TEXT,
  creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  asignado_a_id BIGINT REFERENCES app.usuarios(id),
  resuelto_en TIMESTAMPTZ,
  fuente VARCHAR(16) NOT NULL DEFAULT 'app'
);

CREATE TABLE IF NOT EXISTS app.eventos_alerta (
  id BIGSERIAL PRIMARY KEY,
  alerta_id BIGINT NOT NULL REFERENCES app.alertas(id) ON DELETE CASCADE,
  por_usuario_id BIGINT REFERENCES app.usuarios(id),
  tipo VARCHAR(32) NOT NULL,
  detalle_json JSONB NOT NULL DEFAULT '{}'::JSONB,
  creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO app.roles (nombre) VALUES ('user'),('nurse') ON CONFLICT (nombre) DO NOTHING;
INSERT INTO app.tipos_alerta (codigo, nombre, activo) VALUES ('trauma','Trauma', TRUE) ON CONFLICT (codigo) DO NOTHING;
"""


class AlertsFlowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with connection.cursor() as cursor:
            cursor.execute(DDL)
        from accounts.models import Usuario, Role
        nurse_role = Role.objects.get(nombre="nurse")
        user_role = Role.objects.get(nombre="user")
        cls.nurse = Usuario.objects.create(email="nurse2@example.com", pass_hash=make_password("Secret123!"), rol=nurse_role, activo=True)
        cls.patient = Usuario.objects.create(email="patient3@example.com", pass_hash=make_password("Secret123!"), rol=user_role, activo=True)
        cls.user_access = create_access_token({"sub": str(cls.patient.id), "email": cls.patient.email, "role": "user"}, 600)
        cls.nurse_access = create_access_token({"sub": str(cls.nurse.id), "email": cls.nurse.email, "role": "nurse"}, 600)

    def test_full_alert_flow(self):
        # User crea alerta
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_access}")
        res = c.post(reverse("alerts"), {"latitud": -17.78, "longitud": -63.19, "descripcion": "Prueba", "tipo_alerta_codigo": "trauma"}, format="json")
        self.assertEqual(res.status_code, 201)
        alert_id = res.data["id"]

        # Nurse lista todas y ve la alerta
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {self.nurse_access}")
        res = c.get(reverse("alerts"))
        self.assertEqual(res.status_code, 200)
        self.assertTrue(any(a["id"] == alert_id for a in res.data))

        # Nurse asigna
        res = c.post(reverse("alert-assign", args=[alert_id]), {}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["estado"], "en_curso")

        # Nurse resuelve
        res = c.post(reverse("alert-status", args=[alert_id]), {"estado": "resuelta"}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["estado"], "resuelta")
from django.test import TestCase

# Create your tests here.
