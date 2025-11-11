from django.db import models
from accounts.models import Usuario


class TipoAlerta(models.Model):
    id = models.BigAutoField(primary_key=True)
    codigo = models.CharField(max_length=32, unique=True)
    nombre = models.CharField(max_length=80)
    activo = models.BooleanField(default=True)

    class Meta:
        managed = False
        db_table = 'app"."tipos_alerta'
        verbose_name = "Tipo de alerta"
        verbose_name_plural = "Tipos de alerta"


class Alerta(models.Model):
    id = models.BigAutoField(primary_key=True)
    paciente = models.ForeignKey(Usuario, on_delete=models.SET_NULL, db_column="paciente_id", blank=True, null=True, related_name="alertas")
    tipo_alerta = models.ForeignKey(TipoAlerta, on_delete=models.SET_NULL, db_column="tipo_alerta_id", blank=True, null=True)
    estado = models.CharField(max_length=20, default="pendiente")
    latitud = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitud = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    asignado_a = models.ForeignKey(Usuario, on_delete=models.SET_NULL, db_column="asignado_a_id", blank=True, null=True, related_name="alertas_asignadas")
    resuelto_en = models.DateTimeField(blank=True, null=True)
    fuente = models.CharField(max_length=16, default="app")

    class Meta:
        managed = False
        db_table = 'app"."alertas'
        verbose_name = "Alerta"
        verbose_name_plural = "Alertas"


class EventoAlerta(models.Model):
    id = models.BigAutoField(primary_key=True)
    alerta = models.ForeignKey(Alerta, on_delete=models.CASCADE, db_column="alerta_id", related_name="eventos")
    por_usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, db_column="por_usuario_id", blank=True, null=True)
    tipo = models.CharField(max_length=32)
    detalle_json = models.JSONField(default=dict)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'app"."eventos_alerta'
        verbose_name = "Evento de alerta"
        verbose_name_plural = "Eventos de alerta"
from django.db import models

# Create your models here.
