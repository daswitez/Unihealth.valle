from django.db import models
from accounts.models import Usuario


class TipoServicio(models.Model):
    id = models.BigAutoField(primary_key=True)
    codigo = models.CharField(max_length=32, unique=True)
    nombre = models.CharField(max_length=80)
    activo = models.BooleanField(default=True)

    class Meta:
        managed = False
        db_table = 'app"."tipos_servicio'
        verbose_name = "Tipo de servicio"
        verbose_name_plural = "Tipos de servicio"


class Agenda(models.Model):
    id = models.BigAutoField(primary_key=True)
    enfermero = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column="enfermero_id", related_name="agendas")
    dia_semana = models.SmallIntegerField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    class Meta:
        managed = False
        db_table = 'app"."agendas'
        verbose_name = "Agenda"
        verbose_name_plural = "Agendas"


class Cita(models.Model):
    id = models.BigAutoField(primary_key=True)
    paciente = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column="paciente_id", related_name="citas_paciente")
    enfermero = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column="enfermero_id", related_name="citas_enfermero")
    tipo_servicio = models.ForeignKey(TipoServicio, on_delete=models.CASCADE, db_column="tipo_servicio_id")
    inicio = models.DateTimeField()
    fin = models.DateTimeField()
    estado = models.CharField(max_length=20, default="solicitada")
    motivo = models.TextField(blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'app"."citas'
        verbose_name = "Cita"
        verbose_name_plural = "Citas"
from django.db import models

# Create your models here.
