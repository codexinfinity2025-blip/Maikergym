from django.db import transaction
from django.utils import timezone

from .models import (
    AsignacionPlanUsuario,
    EstadoAsignacionChoice,
    HorarioPlanUsuario,
    NivelEjercicioChoice,
    PlanEntrenamiento,
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