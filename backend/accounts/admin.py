from django.contrib import admin

from .models import Role, Usuario


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """
    Catálogo de roles en solo lectura.
    """

    list_display = ("id", "nombre", "descripcion")
    search_fields = ("nombre",)
    readonly_fields = ("id", "nombre", "descripcion")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    """
    Usuarios en solo lectura para inspección.
    """

    list_display = ("id", "email", "rol", "activo", "creado_en", "actualizado_en", "ultimo_login")
    list_filter = ("activo", "rol__nombre")
    search_fields = ("email",)
    readonly_fields = ("id", "email", "rol", "activo", "creado_en", "actualizado_en", "ultimo_login", "pass_hash")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
from django.contrib import admin

# Register your models here.
