from django.contrib import admin
from gym_project.gym_app.models import Ejercicio, PerfilUsuario

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



@admin.register(Ejercicio)
class EjercicioAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "grupo_muscular",
        "nivel",
        "tipo_equipo",
        "tipo_medicion",
        "puntos_base",
        "activo",
    )
    list_filter = (
        "grupo_muscular",
        "nivel",
        "tipo_equipo",
        "tipo_medicion",
        "activo",
    )
    search_fields = (
        "nombre",
        "descripcion",
        "musculos_secundarios",
        "equipo_necesario",
    )
    readonly_fields = (
        "slug",
        "fecha_creacion",
        "fecha_actualizacion",
    )
    list_editable = (
        "puntos_base",
        "activo",
    )
    ordering = (
        "grupo_muscular",
        "nombre",
    )

    fieldsets = (
        ("Identificación", {
            "fields": (
                "nombre",
                "slug",
                "activo",
            )
        }),
        ("Clasificación", {
            "fields": (
                "grupo_muscular",
                "musculos_secundarios",
                "nivel",
                "tipo_equipo",
                "equipo_necesario",
                "tipo_medicion",
            )
        }),
        ("Técnica y seguridad", {
            "fields": (
                "descripcion",
                "instrucciones",
                "errores_comunes",
                "precauciones",
            )
        }),
        ("Gamificación", {
            "fields": (
                "puntos_base",
            )
        }),
        ("Multimedia", {
            "fields": (
                "imagen_portada",
                "modelo_3d",
            )
        }),
        ("Fechas", {
            "fields": (
                "fecha_creacion",
                "fecha_actualizacion",
            ),
            "classes": (
                "collapse",
            ),
        }),
    )