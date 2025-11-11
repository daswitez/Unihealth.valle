from django.db import models
from accounts.models import Usuario


class PerfilPaciente(models.Model):
    """
    Mapea a app.perfiles_paciente (1:1 con usuario).
    """

    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, db_column="usuario_id", primary_key=True, related_name="perfil")
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    sexo = models.CharField(max_length=1, blank=True, null=True)  # 'M','F','X' o null
    contacto_emergencia = models.CharField(max_length=100, blank=True, null=True)
    alergias = models.TextField(blank=True, null=True)
    antecedentes = models.TextField(blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'app"."perfiles_paciente'
        verbose_name = "Perfil de paciente"
        verbose_name_plural = "Perfiles de paciente"


class Consentimiento(models.Model):
    """
    Mapea a app.consentimientos (histórico de versiones aceptadas).
    """

    id = models.BigAutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column="usuario_id", related_name="consentimientos")
    version = models.CharField(max_length=20)
    aceptado_en = models.DateTimeField(auto_now_add=True)
    ip = models.GenericIPAddressField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'app"."consentimientos'
        verbose_name = "Consentimiento"
        verbose_name_plural = "Consentimientos"

# Create your models here.
