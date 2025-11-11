from django.core.management.base import BaseCommand
from django.db import connection, transaction


SQL = """
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

INSERT INTO app.roles (nombre, descripcion) VALUES
('user','Usuario estándar'),
('nurse','Enfermería'),
('admin','Administrador'),
('auditor','Auditor')
ON CONFLICT (nombre) DO NOTHING;
"""


class Command(BaseCommand):
    help = "Crea el esquema 'app' y las tablas base (roles, usuarios) con roles semilla."

    def handle(self, *args, **options):
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(SQL)
        self.stdout.write(self.style.SUCCESS("Esquema y tablas base creadas (app.roles, app.usuarios)."))

