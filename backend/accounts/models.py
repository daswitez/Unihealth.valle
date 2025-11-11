from django.db import models


class Role(models.Model):
    """
    Modelo mapeado a app.roles (catálogo de roles).
    managed=False para respetar la BD existente.
    """

    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=32, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'app"."roles'  # para que Django genere "app"."roles"
        verbose_name = "Rol"
        verbose_name_plural = "Roles"

    def __str__(self) -> str:
        return self.nombre


class Usuario(models.Model):
    """
    Modelo mapeado a app.usuarios (usuarios del sistema).
    managed=False para respetar la BD existente.
    """

    id = models.BigAutoField(primary_key=True)
    email = models.CharField(max_length=254, unique=True)
    pass_hash = models.TextField()
    rol = models.ForeignKey(Role, on_delete=models.DO_NOTHING, db_column="rol_id")
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    ultimo_login = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'app"."usuarios'  # para que Django genere "app"."usuarios"
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self) -> str:
        return f"{self.email} ({self.rol.nombre})"

# Create your models here.
