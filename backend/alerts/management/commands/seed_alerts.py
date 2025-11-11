from django.core.management.base import BaseCommand
from django.db import connection, transaction


SQL = """
CREATE SCHEMA IF NOT EXISTS app;

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
  estado VARCHAR(20) NOT NULL DEFAULT 'pendiente' CHECK (estado IN ('pendiente','en_curso','resuelta')),
  latitud NUMERIC(9,6),
  longitud NUMERIC(9,6),
  descripcion TEXT,
  creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  asignado_a_id BIGINT REFERENCES app.usuarios(id),
  resuelto_en TIMESTAMPTZ,
  fuente VARCHAR(16) NOT NULL DEFAULT 'app' CHECK (fuente IN ('app','kiosco','admin'))
);

CREATE TABLE IF NOT EXISTS app.eventos_alerta (
  id BIGSERIAL PRIMARY KEY,
  alerta_id BIGINT NOT NULL REFERENCES app.alertas(id) ON DELETE CASCADE,
  por_usuario_id BIGINT REFERENCES app.usuarios(id),
  tipo VARCHAR(32) NOT NULL CHECK (tipo IN ('creada','asignada','cambio_estado','nota','adjunto')),
  detalle_json JSONB NOT NULL DEFAULT '{}'::JSONB,
  creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO app.tipos_alerta (codigo, nombre, activo) VALUES
('trauma','Trauma', TRUE),
('cardio','Cardiovascular', TRUE),
('otro','Otro', TRUE)
ON CONFLICT (codigo) DO NOTHING;
"""


class Command(BaseCommand):
    help = "Crea tablas de alertas y semillas de tipos_alerta."

    def handle(self, *args, **options):
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(SQL)
        self.stdout.write(self.style.SUCCESS("Esquema de alertas listo y tipos_alerta sembrados."))

