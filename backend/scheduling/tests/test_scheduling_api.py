from datetime import time

from django.test import TestCase
from django.urls import reverse
from django.db import connection
from django.utils import timezone
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

CREATE TABLE IF NOT EXISTS app.tipos_servicio (
  id BIGSERIAL PRIMARY KEY,
  codigo VARCHAR(32) NOT NULL UNIQUE,
  nombre VARCHAR(80) NOT NULL,
  activo BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS app.agendas (
  id BIGSERIAL PRIMARY KEY,
  enfermero_id BIGINT NOT NULL REFERENCES app.usuarios(id),
  dia_semana SMALLINT NOT NULL,
  hora_inicio TIME NOT NULL,
  hora_fin TIME NOT NULL
);

CREATE TABLE IF NOT EXISTS app.citas (
  id BIGSERIAL PRIMARY KEY,
  paciente_id BIGINT NOT NULL REFERENCES app.usuarios(id),
  enfermero_id BIGINT NOT NULL REFERENCES app.usuarios(id),
  tipo_servicio_id BIGINT NOT NULL REFERENCES app.tipos_servicio(id),
  inicio TIMESTAMPTZ NOT NULL,
  fin TIMESTAMPTZ NOT NULL,
  estado VARCHAR(20) NOT NULL DEFAULT 'solicitada',
  motivo TEXT,
  creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO app.roles (nombre) VALUES ('user'),('nurse') ON CONFLICT (nombre) DO NOTHING;
INSERT INTO app.tipos_servicio (codigo, nombre, activo) VALUES ('control','Control general', TRUE) ON CONFLICT (codigo) DO NOTHING;
"""


class SchedulingTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with connection.cursor() as cursor:
            cursor.execute(DDL)
        from accounts.models import Usuario, Role
        cls.nurse_role = Role.objects.get(nombre="nurse")
        cls.user_role = Role.objects.get(nombre="user")
        cls.nurse = Usuario.objects.create(email="nurse_sched@example.com", pass_hash=make_password("Secret123!"), rol=cls.nurse_role, activo=True)
        cls.patient = Usuario.objects.create(email="patient_sched@example.com", pass_hash=make_password("Secret123!"), rol=cls.user_role, activo=True)
        # Agenda del día de prueba (usar día actual para slots)
        today = timezone.localdate()
        weekday = today.weekday()
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO app.agendas(enfermero_id,dia_semana,hora_inicio,hora_fin) VALUES (%s,%s,%s,%s)",
                [cls.nurse.id, weekday, time(9, 0), time(12, 0)],
            )
        cls.nurse_access = create_access_token({"sub": str(cls.nurse.id), "email": cls.nurse.email, "role": "nurse"}, 600)
        cls.user_access = create_access_token({"sub": str(cls.patient.id), "email": cls.patient.email, "role": "user"}, 600)
        cls.today = today

    def test_slots_and_conflict(self):
        c = APIClient()
        # Nurse consulta slots del día
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {self.nurse_access}")
        res = c.get(reverse("appointments-slots"), {"enfermero_id": self.nurse.id, "date": str(self.today)})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(len(res.data) > 0)
        first_slot = res.data[0]
        start = first_slot["start"]
        end = first_slot["end"]

        # User crea cita en ese slot
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_access}")
        res = c.post(
            reverse("appointments"),
            {
                "paciente_id": self.patient.id,
                "enfermero_id": self.nurse.id,
                "tipo_servicio_codigo": "control",
                "start_ts": start,
                "end_ts": end,
                "reason": "Chequeo",
            },
            format="json",
        )
        self.assertEqual(res.status_code, 201)

        # Intentar crear otra cita solapada (conflicto)
        res = c.post(
            reverse("appointments"),
            {
                "paciente_id": self.patient.id,
                "enfermero_id": self.nurse.id,
                "tipo_servicio_codigo": "control",
                "start_ts": start,
                "end_ts": end,
                "reason": "Otro",
            },
            format="json",
        )
        self.assertEqual(res.status_code, 409)

