from django.core.management.base import BaseCommand
from django.db import connection, transaction


SQL = """
CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS app.tipos_nota (
  id BIGSERIAL PRIMARY KEY,
  codigo VARCHAR(32) NOT NULL UNIQUE,
  nombre VARCHAR(80) NOT NULL,
  activo BOOLEAN NOT NULL DEFAULT TRUE
);

INSERT INTO app.tipos_nota (codigo, nombre, activo) VALUES
('triaje','Nota de triaje', TRUE),
('evol','Evolución', TRUE),
('resumen','Resumen clínico', TRUE)
ON CONFLICT (codigo) DO NOTHING;
"""


class Command(BaseCommand):
    help = "Crea/asegura tipos de nota mínimos (triaje, evol, resumen)."

    def handle(self, *args, **options):
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(SQL)
        self.stdout.write(self.style.SUCCESS("Tipos de nota sembrados/asegurados (triaje, evol, resumen)."))

