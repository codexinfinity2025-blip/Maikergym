from django.contrib import admin
from gym_project.gym_app.models import PerfilUsuario

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'rol', 'objetivo', 'dieta_aceptada', 'datos_completos', 'fecha_registro', 'activo')
    list_filter = ('rol', 'objetivo', 'dieta_aceptada', 'datos_completos', 'activo', 'fecha_registro')
    search_fields = ('user__email', 'user__username', 'user__first_name', 'user__last_name')
    readonly_fields = ('fecha_registro',)

    fieldsets = (
        ('InformaciÃ³n del Usuario', {
            'fields': ('user', 'rol', 'activo')
        }),
        ('PersonalizaciÃ³n', {
            'fields': ('objetivo', 'dieta_aceptada', 'foto', 'genero', 'peso', 'edad', 'datos_completos')
        }),
        ('Fechas', {
            'fields': ('fecha_registro',),
            'classes': ('collapse',)
        }),
    )