from decimal import Decimal, InvalidOperation
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
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
    TipoMedicionChoice,
    EstadoSerieChoice,
    SerieEjercicioSesion,
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
            semana_plan=semana_actual,
            dia_plan=dia_plan,
        )
        .first()
    )

    sesion_creada = False

    if sesion is None:
        sesion_misma_fecha = (
            SesionEntrenamiento.objects
            .select_for_update()
            .filter(
                asignacion=asignacion,
                fecha=hoy,
            )
            .first()
        )

        if sesion_misma_fecha is not None:
            raise ValidationError(
                "Ya existe otra sesión para esta fecha."
            )

        sesion = SesionEntrenamiento.objects.create(
            asignacion=asignacion,
            dia_plan=dia_plan,
            fecha=hoy,
            semana_plan=semana_actual,
            estado=EstadoSesionChoice.EN_PROGRESO,
            fecha_inicio=timezone.now(),
        )
        sesion_creada = True

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

    asegurar_series_sesion(sesion)
    return sesion, sesion_creada

def _convertir_entero(
    valor,
    nombre_campo,
    requerido=False,
):
    if valor is None or str(valor).strip() == "":
        if requerido:
            raise ValidationError(
                f"Debes indicar {nombre_campo}."
            )
        return None

    try:
        resultado = int(valor)
    except (TypeError, ValueError):
        raise ValidationError(
            f"{nombre_campo.capitalize()} debe ser un número entero."
        )

    if resultado < 0:
        raise ValidationError(
            f"{nombre_campo.capitalize()} no puede ser negativo."
        )

    return resultado


def _convertir_decimal(
    valor,
    nombre_campo,
):
    if valor is None or str(valor).strip() == "":
        return None

    try:
        resultado = Decimal(
            str(valor).strip().replace(",", ".")
        )
    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError(
            f"{nombre_campo.capitalize()} debe ser un número válido."
        )

    if resultado < 0:
        raise ValidationError(
            f"{nombre_campo.capitalize()} no puede ser negativo."
        )

    if resultado > Decimal("9999.99"):
        raise ValidationError(
            f"{nombre_campo.capitalize()} es demasiado alto."
        )

    return resultado


@transaction.atomic
def completar_ejercicio_sesion(
    usuario,
    ejercicio_sesion_id,
    series_completadas,
    repeticiones_realizadas=None,
    duracion_realizada_segundos=None,
    distancia_realizada_metros=None,
    peso_utilizado_kg=None,
    observaciones="",
):
    try:
        registro = (
            EjercicioSesion.objects
            .select_for_update()
            .select_related(
                "ejercicio_programado__ejercicio"
            )
            .get(pk=ejercicio_sesion_id)
        )
    except EjercicioSesion.DoesNotExist:
        raise ValidationError(
            "No se encontró el ejercicio solicitado."
        )

    sesion = (
        SesionEntrenamiento.objects
        .select_for_update()
        .select_related("asignacion__usuario")
        .get(pk=registro.sesion_id)
    )

    if sesion.asignacion.usuario_id != usuario.id:
        raise ValidationError(
            "No tienes permiso para modificar este ejercicio."
        )

    if registro.completado:
        return registro, False, sesion

    programado = registro.ejercicio_programado
    ejercicio = programado.ejercicio

    series = _convertir_entero(
        series_completadas,
        "las series completadas",
        requerido=True,
    )

    if series == 0:
        raise ValidationError(
            "Debes completar al menos una serie."
        )

    if series < programado.series:
        raise ValidationError(
            f"Debes completar las {programado.series} "
            "series programadas."
        )

    if series > 20:
        raise ValidationError(
            "No puedes registrar más de 20 series."
        )

    repeticiones = None
    duracion = None
    distancia = None

    if ejercicio.tipo_medicion == TipoMedicionChoice.REPETICIONES:
        repeticiones = _convertir_entero(
            repeticiones_realizadas,
            "las repeticiones por serie",
            requerido=True,
        )

        if (
            programado.repeticiones_min is not None
            and repeticiones < programado.repeticiones_min
        ):
            raise ValidationError(
                "Debes realizar al menos "
                f"{programado.repeticiones_min} "
                "repeticiones por serie."
            )

    elif ejercicio.tipo_medicion == TipoMedicionChoice.TIEMPO:
        duracion = _convertir_entero(
            duracion_realizada_segundos,
            "la duración en segundos",
            requerido=True,
        )

        if (
            programado.duracion_segundos is not None
            and duracion < programado.duracion_segundos
        ):
            raise ValidationError(
                "Debes completar al menos "
                f"{programado.duracion_segundos} segundos."
            )

    elif ejercicio.tipo_medicion == TipoMedicionChoice.DISTANCIA:
        distancia = _convertir_entero(
            distancia_realizada_metros,
            "la distancia en metros",
            requerido=True,
        )

        if (
            programado.distancia_metros is not None
            and distancia < programado.distancia_metros
        ):
            raise ValidationError(
                "Debes completar al menos "
                f"{programado.distancia_metros} metros."
            )

    peso = _convertir_decimal(
        peso_utilizado_kg,
        "el peso utilizado",
    )

    registro.series_completadas = series
    registro.repeticiones_realizadas = repeticiones
    registro.duracion_realizada_segundos = duracion
    registro.distancia_realizada_metros = distancia
    registro.peso_utilizado_kg = peso
    registro.observaciones = (
        str(observaciones or "").strip()[:250]
    )
    registro.puntos_obtenidos = ejercicio.puntos_base
    registro.completado = True
    registro.fecha_completado = timezone.now()

    registro.full_clean()
    registro.save()

    puntos_totales = (
        sesion.ejercicios
        .filter(completado=True)
        .aggregate(total=Sum("puntos_obtenidos"))
        .get("total")
        or 0
    )

    quedan_obligatorios = (
        sesion.ejercicios
        .filter(
            ejercicio_programado__obligatorio=True,
            ejercicio_programado__activo=True,
            completado=False,
        )
        .exists()
    )

    sesion.puntos_obtenidos = puntos_totales

    if quedan_obligatorios:
        sesion.estado = EstadoSesionChoice.EN_PROGRESO
    else:
        sesion.estado = EstadoSesionChoice.COMPLETADA

        if sesion.fecha_finalizacion is None:
            sesion.fecha_finalizacion = timezone.now()

    sesion.save(
        update_fields=[
            "puntos_obtenidos",
            "estado",
            "fecha_finalizacion",
            "fecha_actualizacion",
        ]
    )

    return registro, True, sesion

@transaction.atomic
def asegurar_series_sesion(sesion):
    sesion = (
        SesionEntrenamiento.objects
        .select_for_update()
        .get(pk=sesion.pk)
    )

    ejercicios_sesion = (
        sesion.ejercicios
        .select_related(
            "ejercicio_programado"
        )
        .prefetch_related("series")
    )

    series_nuevas = []

    for ejercicio_sesion in ejercicios_sesion:
        numeros_existentes = {
            serie.numero
            for serie in ejercicio_sesion.series.all()
        }

        programado = (
            ejercicio_sesion.ejercicio_programado
        )

        estado_inicial = EstadoSerieChoice.PENDIENTE
        fecha_inicio = None
        fecha_finalizacion = None

        if ejercicio_sesion.completado:
            estado_inicial = EstadoSerieChoice.COMPLETADA
            fecha_finalizacion = (
                ejercicio_sesion.fecha_completado
                or sesion.fecha_finalizacion
                or timezone.now()
            )
            fecha_inicio = (
                sesion.fecha_inicio
                or fecha_finalizacion
            )

        for numero in range(
            1,
            programado.series + 1,
        ):
            if numero in numeros_existentes:
                continue

            series_nuevas.append(
                SerieEjercicioSesion(
                    ejercicio_sesion=ejercicio_sesion,
                    numero=numero,
                    estado=estado_inicial,
                    repeticiones_realizadas=(
                        ejercicio_sesion
                        .repeticiones_realizadas
                    ),
                    duracion_realizada_segundos=(
                        ejercicio_sesion
                        .duracion_realizada_segundos
                    ),
                    distancia_realizada_metros=(
                        ejercicio_sesion
                        .distancia_realizada_metros
                    ),
                    peso_utilizado_kg=(
                        ejercicio_sesion
                        .peso_utilizado_kg
                    ),
                    fecha_inicio=fecha_inicio,
                    fecha_finalizacion=fecha_finalizacion,
                )
            )

    if series_nuevas:
        SerieEjercicioSesion.objects.bulk_create(
            series_nuevas,
            ignore_conflicts=True,
        )

    return len(series_nuevas)