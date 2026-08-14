from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import (
    AsignacionPlanUsuario,
    EjercicioSesion,
    EstadoAsignacionChoice,
    EstadoSesionChoice,
    HorarioPlanUsuario,
    NivelEjercicioChoice,
    PlanEntrenamiento,
    SesionEntrenamiento,
)


DIAS_SEMANA_POR_CANTIDAD = {
    1: [0],
    2: [0, 3],
    3: [0, 2, 4],
    4: [0, 1, 3, 4],
    5: [0, 1, 2, 3, 4],
    6: [0, 1, 2, 3, 4, 5],
    7: [0, 1, 2, 3, 4, 5, 6],
}


@transaction.atomic
def asignar_plan_por_objetivo(usuario, objetivo):
    plan = (
        PlanEntrenamiento.objects
        .filter(
            objetivo=objetivo,
            nivel=NivelEjercicioChoice.PRINCIPIANTE,
            activo=True,
        )
        .order_by("id")
        .first()
    )

    if plan is None:
        return None, False

    asignacion_actual = (
        AsignacionPlanUsuario.objects
        .select_for_update()
        .select_related("plan")
        .filter(
            usuario=usuario,
            estado=EstadoAsignacionChoice.ACTIVO,
        )
        .first()
    )

    if (
        asignacion_actual is not None
        and asignacion_actual.plan_id == plan.id
    ):
        return asignacion_actual, False

    hoy = timezone.localdate()

    if asignacion_actual is not None:
        asignacion_actual.estado = EstadoAsignacionChoice.ABANDONADO
        asignacion_actual.fecha_fin = max(
            hoy,
            asignacion_actual.fecha_inicio,
        )
        asignacion_actual.save(
            update_fields=[
                "estado",
                "fecha_fin",
                "fecha_actualizacion",
            ]
        )

    asignacion = AsignacionPlanUsuario.objects.create(
        usuario=usuario,
        plan=plan,
        fecha_inicio=hoy,
    )

    dias_semana = DIAS_SEMANA_POR_CANTIDAD[
        plan.dias_por_semana
    ]

    horarios = [
        HorarioPlanUsuario(
            asignacion=asignacion,
            numero_dia_plan=numero_dia,
            dia_semana=dia_semana,
            hora_preferida=None,
            recordatorio_activo=False,
            activo=True,
        )
        for numero_dia, dia_semana in enumerate(
            dias_semana,
            start=1,
        )
    ]

    HorarioPlanUsuario.objects.bulk_create(horarios)

    return asignacion, True

@transaction.atomic
def iniciar_sesion_entrenamiento(
    asignacion,
    dia_plan,
):
    asignacion = (
        AsignacionPlanUsuario.objects
        .select_for_update()
        .select_related("plan")
        .get(pk=asignacion.pk)
    )

    if asignacion.estado != EstadoAsignacionChoice.ACTIVO:
        raise ValidationError(
            "El usuario no tiene un plan activo."
        )

    hoy = timezone.localdate()
    semana_actual = asignacion.semana_actual
    fase_actual = asignacion.fase_actual

    if semana_actual <= 0:
        raise ValidationError(
            "El plan todavía no ha comenzado."
        )

    if (
        fase_actual is None
        or dia_plan.fase_id != fase_actual.id
    ):
        raise ValidationError(
            "Este entrenamiento no pertenece "
            "a la fase actual."
        )

    horario = asignacion.horarios.filter(
        numero_dia_plan=dia_plan.numero,
        dia_semana=hoy.weekday(),
        activo=True,
    ).first()

    if horario is None:
        raise ValidationError(
            "Este entrenamiento no corresponde "
            "al día de hoy."
        )

    sesion = (
        SesionEntrenamiento.objects
        .select_for_update()
        .filter(
            asignacion=asignacion,
            fecha=hoy,
        )
        .first()
    )

    sesion_creada = False

    if sesion is None:
        sesion = SesionEntrenamiento.objects.create(
            asignacion=asignacion,
            dia_plan=dia_plan,
            fecha=hoy,
            semana_plan=semana_actual,
            estado=EstadoSesionChoice.EN_PROGRESO,
            fecha_inicio=timezone.now(),
        )
        sesion_creada = True

    elif sesion.dia_plan_id != dia_plan.id:
        raise ValidationError(
            "Ya existe otra sesión para esta fecha."
        )

    elif sesion.estado == EstadoSesionChoice.PENDIENTE:
        sesion.estado = EstadoSesionChoice.EN_PROGRESO
        sesion.fecha_inicio = timezone.now()
        sesion.save(
            update_fields=[
                "estado",
                "fecha_inicio",
                "fecha_actualizacion",
            ]
        )

    ejercicios_programados = (
        dia_plan.ejercicios_programados
        .filter(
            activo=True,
            ejercicio__activo=True,
        )
        .select_related("ejercicio")
    )

    ejercicios_existentes = set(
        sesion.ejercicios.values_list(
            "ejercicio_programado_id",
            flat=True,
        )
    )

    ejercicios_nuevos = [
        EjercicioSesion(
            sesion=sesion,
            ejercicio_programado=programado,
        )
        for programado in ejercicios_programados
        if programado.id not in ejercicios_existentes
    ]

    if ejercicios_nuevos:
        EjercicioSesion.objects.bulk_create(
            ejercicios_nuevos,
            ignore_conflicts=True,
        )

    return sesion, sesion_creada