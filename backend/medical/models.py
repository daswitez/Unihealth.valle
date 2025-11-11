from django.db import models
from accounts.models import Usuario


class TipoNota(models.Model):
    id = models.BigAutoField(primary_key=True)
    codigo = models.CharField(max_length=32, unique=True)
    nombre = models.CharField(max_length=80)
    activo = models.BooleanField(default=True)

    class Meta:
        managed = False
        db_table = 'app"."tipos_nota'
        verbose_name = "Tipo de nota"
        verbose_name_plural = "Tipos de nota"


class RegistroClinico(models.Model):
    id = models.BigAutoField(primary_key=True)
    paciente = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column="paciente_id", related_name="registros_clinicos")
    creado_por = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING, db_column="creado_por_id", related_name="registros_clinicos_creados")
    tipo_nota = models.ForeignKey(TipoNota, on_delete=models.DO_NOTHING, db_column="tipo_nota_id")
    nota = models.TextField(blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'app"."registros_clinicos'
        verbose_name = "Registro clínico"
        verbose_name_plural = "Registros clínicos"


class SignoVital(models.Model):
    id = models.BigAutoField(primary_key=True)
    paciente = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column="paciente_id", related_name="signos_vitales")
    tomado_por = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING, db_column="tomado_por_id", related_name="signos_tomados")
    pas_sistolica = models.SmallIntegerField(blank=True, null=True)
    pas_diastolica = models.SmallIntegerField(blank=True, null=True)
    fcritmo = models.SmallIntegerField(blank=True, null=True)
    temp_c = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    spo2 = models.SmallIntegerField(blank=True, null=True)
    tomado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'app"."signos_vitales'
        verbose_name = "Signo vital"
        verbose_name_plural = "Signos vitales"


class Adjunto(models.Model):
    id = models.BigAutoField(primary_key=True)
    propietario_tabla = models.CharField(max_length=32)
    propietario_id = models.BigIntegerField()
    nombre_archivo = models.TextField()
    mime = models.CharField(max_length=100)
    ruta_storage = models.TextField(unique=True)
    tamano_bytes = models.IntegerField()
    creado_por = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING, db_column="creado_por_id")
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'app"."adjuntos'
        verbose_name = "Adjunto"
        verbose_name_plural = "Adjuntos"
from django.db import models

# Create your models here.
