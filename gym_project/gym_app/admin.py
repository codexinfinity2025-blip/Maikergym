from django.contrib import admin
from gym_project.gym_app.models import (
    DiaPlan,
    Ejercicio,
    EjercicioProgramado,
    FasePlan,
    PerfilUsuario,
    PlanEntrenamiento,
)

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

class FasePlanInline(admin.TabularInline):
    model = FasePlan
    extra = 0
    fields = (
        "orden",
        "nombre",
        "semana_inicio",
        "semana_fin",
        "activo",
    )
    show_change_link = True


@admin.register(PlanEntrenamiento)
class PlanEntrenamientoAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "objetivo",
        "nivel",
        "duracion_semanas",
        "dias_por_semana",
        "activo",
    )
    list_filter = (
        "objetivo",
        "nivel",
        "activo",
    )
    search_fields = (
        "nombre",
        "descripcion",
    )
    readonly_fields = (
        "slug",
        "fecha_creacion",
        "fecha_actualizacion",
    )
    inlines = [
        FasePlanInline,
    ]

    fieldsets = (
        ("Información principal", {
            "fields": (
                "nombre",
                "slug",
                "objetivo",
                "nivel",
                "descripcion",
            )
        }),
        ("Programación", {
            "fields": (
                "duracion_semanas",
                "dias_por_semana",
                "activo",
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


class DiaPlanInline(admin.TabularInline):
    model = DiaPlan
    extra = 0
    fields = (
        "numero",
        "nombre",
        "enfoque",
        "activo",
    )
    show_change_link = True


@admin.register(FasePlan)
class FasePlanAdmin(admin.ModelAdmin):
    list_display = (
        "plan",
        "orden",
        "nombre",
        "semana_inicio",
        "semana_fin",
        "activo",
    )
    list_filter = (
        "plan",
        "activo",
    )
    search_fields = (
        "nombre",
        "plan__nombre",
    )
    inlines = [
        DiaPlanInline,
    ]


class EjercicioProgramadoInline(admin.TabularInline):
    model = EjercicioProgramado
    extra = 0
    autocomplete_fields = (
        "ejercicio",
    )
    fields = (
        "orden",
        "ejercicio",
        "series",
        "repeticiones_min",
        "repeticiones_max",
        "duracion_segundos",
        "distancia_metros",
        "descanso_segundos",
        "esfuerzo_objetivo",
        "obligatorio",
        "activo",
    )
    show_change_link = True


@admin.register(DiaPlan)
class DiaPlanAdmin(admin.ModelAdmin):
    list_display = (
        "fase",
        "numero",
        "nombre",
        "enfoque",
        "activo",
    )
    list_filter = (
        "fase__plan",
        "fase",
        "activo",
    )
    search_fields = (
        "nombre",
        "enfoque",
        "fase__nombre",
        "fase__plan__nombre",
    )
    inlines = [
        EjercicioProgramadoInline,
    ]


@admin.register(EjercicioProgramado)
class EjercicioProgramadoAdmin(admin.ModelAdmin):
    list_display = (
        "dia",
        "orden",
        "ejercicio",
        "series",
        "repeticiones_min",
        "repeticiones_max",
        "duracion_segundos",
        "distancia_metros",
        "obligatorio",
        "activo",
    )
    list_filter = (
        "dia__fase__plan",
        "ejercicio__grupo_muscular",
        "obligatorio",
        "activo",
    )
    search_fields = (
        "ejercicio__nombre",
        "dia__nombre",
        "dia__fase__nombre",
        "dia__fase__plan__nombre",
    )
    autocomplete_fields = (
        "ejercicio",
    )