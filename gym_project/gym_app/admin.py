from django.contrib import admin
from gym_project.gym_app.models import (
    AsignacionPlanUsuario,
    DiaPlan,
    Ejercicio,
    EjercicioProgramado,
    EjercicioSesion,
    FasePlan,
    HorarioPlanUsuario,
    PerfilUsuario,
    PlanEntrenamiento,
    SesionEntrenamiento,
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
class HorarioPlanUsuarioInline(admin.TabularInline):
    model = HorarioPlanUsuario
    extra = 0
    fields = (
        "numero_dia_plan",
        "dia_semana",
        "hora_preferida",
        "recordatorio_activo",
        "activo",
    )


@admin.register(AsignacionPlanUsuario)
class AsignacionPlanUsuarioAdmin(admin.ModelAdmin):
    list_display = (
        "usuario",
        "plan",
        "fecha_inicio",
        "mostrar_semana_actual",
        "mostrar_fase_actual",
        "estado",
    )
    list_filter = (
        "plan",
        "estado",
        "fecha_inicio",
    )
    search_fields = (
        "usuario__username",
        "usuario__email",
        "usuario__first_name",
        "usuario__last_name",
        "plan__nombre",
    )
    autocomplete_fields = (
        "usuario",
        "plan",
    )
    readonly_fields = (
        "mostrar_fecha_fin_estimada",
        "mostrar_semana_actual",
        "mostrar_fase_actual",
        "fecha_creacion",
        "fecha_actualizacion",
    )
    inlines = [
        HorarioPlanUsuarioInline,
    ]

    fieldsets = (
        ("Asignación", {
            "fields": (
                "usuario",
                "plan",
                "estado",
            )
        }),
        ("Fechas", {
            "fields": (
                "fecha_inicio",
                "fecha_fin",
                "mostrar_fecha_fin_estimada",
            )
        }),
        ("Progreso calculado", {
            "fields": (
                "mostrar_semana_actual",
                "mostrar_fase_actual",
            )
        }),
        ("Control", {
            "fields": (
                "fecha_creacion",
                "fecha_actualizacion",
            ),
            "classes": (
                "collapse",
            ),
        }),
    )

    @admin.display(description="Fecha final estimada")
    def mostrar_fecha_fin_estimada(self, obj):
        if not obj:
            return "-"

        return obj.fecha_fin_estimada

    @admin.display(description="Semana actual")
    def mostrar_semana_actual(self, obj):
        if not obj:
            return "-"

        return obj.semana_actual

    @admin.display(description="Fase actual")
    def mostrar_fase_actual(self, obj):
        if not obj:
            return "-"

        return obj.fase_actual or "Sin fase"


@admin.register(HorarioPlanUsuario)
class HorarioPlanUsuarioAdmin(admin.ModelAdmin):
    list_display = (
        "asignacion",
        "numero_dia_plan",
        "dia_semana",
        "hora_preferida",
        "recordatorio_activo",
        "activo",
    )
    list_filter = (
        "dia_semana",
        "recordatorio_activo",
        "activo",
    )
    search_fields = (
        "asignacion__usuario__username",
        "asignacion__usuario__email",
        "asignacion__plan__nombre",
    )

class EjercicioSesionInline(admin.TabularInline):
    model = EjercicioSesion
    extra = 0
    fields = (
        "ejercicio_programado",
        "completado",
        "series_completadas",
        "repeticiones_realizadas",
        "duracion_realizada_segundos",
        "distancia_realizada_metros",
        "peso_utilizado_kg",
        "puntos_obtenidos",
        "fecha_completado",
    )
    readonly_fields = (
        "puntos_obtenidos",
        "fecha_completado",
    )
    autocomplete_fields = (
        "ejercicio_programado",
    )


@admin.register(SesionEntrenamiento)
class SesionEntrenamientoAdmin(admin.ModelAdmin):
    list_display = (
        "asignacion",
        "dia_plan",
        "fecha",
        "semana_plan",
        "estado",
        "puntos_obtenidos",
    )
    list_filter = (
        "estado",
        "fecha",
        "semana_plan",
        "asignacion__plan",
    )
    search_fields = (
        "asignacion__usuario__username",
        "asignacion__usuario__email",
        "asignacion__plan__nombre",
        "dia_plan__nombre",
    )
    autocomplete_fields = (
        "asignacion",
        "dia_plan",
    )
    readonly_fields = (
        "puntos_obtenidos",
        "fecha_creacion",
        "fecha_actualizacion",
    )
    inlines = [
        EjercicioSesionInline,
    ]

    fieldsets = (
        ("Entrenamiento", {
            "fields": (
                "asignacion",
                "dia_plan",
                "semana_plan",
                "fecha",
                "estado",
            )
        }),
        ("Resultado", {
            "fields": (
                "puntos_obtenidos",
                "fecha_inicio",
                "fecha_finalizacion",
            )
        }),
        ("Control", {
            "fields": (
                "fecha_creacion",
                "fecha_actualizacion",
            ),
            "classes": (
                "collapse",
            ),
        }),
    )


@admin.register(EjercicioSesion)
class EjercicioSesionAdmin(admin.ModelAdmin):
    list_display = (
        "sesion",
        "ejercicio_programado",
        "completado",
        "series_completadas",
        "puntos_obtenidos",
        "fecha_completado",
    )
    list_filter = (
        "completado",
        "sesion__fecha",
        "sesion__asignacion__plan",
    )
    search_fields = (
        "sesion__asignacion__usuario__username",
        "sesion__asignacion__usuario__email",
        "ejercicio_programado__ejercicio__nombre",
    )
    autocomplete_fields = (
        "sesion",
        "ejercicio_programado",
    )
    readonly_fields = (
        "puntos_obtenidos",
        "fecha_completado",
        "fecha_actualizacion",
    )