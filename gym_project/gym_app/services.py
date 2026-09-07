from datetime import timedelta
from decimal import Decimal, InvalidOperation
from uuid import uuid4
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max, Sum
from django.utils import timezone

from .models import (
    AsignacionPlanUsuario,
    DiaPlan,
    Ejercicio,
    EjercicioProgramado,
    EjercicioSesion,
    EstadoAsignacionChoice,
    EstadoSesionChoice,
    FasePlan,
    HorarioPlanUsuario,
    NivelEjercicioChoice,
    ObjetivoChoice,
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


ENFOQUES_POR_CANTIDAD = {
    1: ["cuerpo_completo"],
    2: ["cuerpo_completo", "cuerpo_completo"],
    3: ["tren_inferior", "empuje", "tiron_core"],
    4: ["tren_inferior", "tren_superior", "piernas_gluteos", "torso_core"],
    5: ["piernas_gluteos", "empuje", "tiron", "tren_inferior", "acondicionamiento"],
    6: ["piernas_gluteos", "empuje", "tiron", "tren_inferior", "torso_core", "acondicionamiento"],
}


NOMBRES_ENFOQUE = {
    "cuerpo_completo": "Cuerpo completo",
    "tren_inferior": "Tren inferior",
    "tren_superior": "Tren superior",
    "piernas_gluteos": "Piernas y glúteos",
    "empuje": "Pecho, hombros y tríceps",
    "tiron": "Espalda y bíceps",
    "tiron_core": "Espalda, bíceps y abdomen",
    "torso_core": "Torso y estabilidad",
    "acondicionamiento": "Acondicionamiento y cuerpo completo",
}


EJERCICIOS_POR_ENFOQUE = {
    "cuerpo_completo": [
        "Sentadilla goblet con mancuerna", "Press de pecho sentado en máquina",
        "Jalón al pecho en polea", "Peso muerto rumano con barra",
        "Press Pallof en polea", "Caminata inclinada en caminadora",
        "Remo en máquina ergométrica", "Bird dog",
    ],
    "tren_inferior": [
        "Sentadilla con barra", "Prensa de piernas en máquina",
        "Peso muerto rumano con barra", "Zancada estática con mancuernas",
        "Extensión de cuádriceps en máquina", "Curl femoral tumbado en máquina",
        "Elevación de talones de pie en máquina", "Puente de glúteos en suelo",
    ],
    "piernas_gluteos": [
        "Sentadilla con barra", "Hip thrust con barra", "Sentadilla goblet con mancuerna",
        "Step-up al banco", "Abducción de cadera en máquina",
        "Curl femoral tumbado en máquina", "Elevación de talones de pie en máquina",
        "Puente de glúteos en suelo",
    ],
    "tren_superior": [
        "Press de banca con barra", "Jalón al pecho en polea",
        "Press militar sentado con mancuernas", "Remo sentado en polea",
        "Face pull en polea", "Curl de bíceps en polea baja",
        "Extensión de tríceps en polea", "Press Pallof en polea",
    ],
    "empuje": [
        "Press de banca con barra", "Press inclinado con mancuernas",
        "Press de pecho sentado en máquina", "Aperturas de pecho en máquina",
        "Press militar sentado con mancuernas", "Elevaciones laterales con mancuernas",
        "Extensión de tríceps en polea", "Extensión de tríceps sobre la cabeza en polea",
    ],
    "tiron": [
        "Jalón al pecho en polea", "Remo sentado en polea", "Remo inclinado con barra",
        "Dominadas asistidas en máquina", "Face pull en polea",
        "Curl de bíceps con barra Z", "Curl martillo con mancuernas",
        "Curl de bíceps en polea baja",
    ],
    "tiron_core": [
        "Jalón al pecho en polea", "Remo sentado en polea", "Face pull en polea",
        "Curl de bíceps con barra Z", "Plancha frontal sobre antebrazos",
        "Crunch abdominal en máquina", "Elevación de rodillas en silla romana", "Bird dog",
    ],
    "torso_core": [
        "Press de pecho sentado en máquina", "Remo sentado en polea",
        "Press militar sentado con mancuernas", "Face pull en polea",
        "Press Pallof en polea", "Plancha frontal sobre antebrazos",
        "Crunch abdominal en máquina", "Bird dog",
    ],
    "acondicionamiento": [
        "Caminata inclinada en caminadora", "Remo en máquina ergométrica",
        "Caminata del granjero con mancuernas", "Step-up al banco",
        "Sentadilla goblet con mancuerna", "Press Pallof en polea",
        "Bird dog", "Puente de glúteos en suelo",
    ],
}


PRIORIDAD_POR_OBJETIVO = {
    ObjetivoChoice.HIPERTROFIA: [
        "Sentadilla con barra", "Press de banca con barra", "Peso muerto rumano con barra",
        "Hip thrust con barra", "Jalón al pecho en polea", "Remo sentado en polea",
    ],
    ObjetivoChoice.ESTETICO: [
        "Sentadilla goblet con mancuerna", "Hip thrust con barra",
        "Press inclinado con mancuernas", "Jalón al pecho en polea",
        "Elevaciones laterales con mancuernas", "Press Pallof en polea",
    ],
    ObjetivoChoice.SALUD: [
        "Sentadilla goblet con mancuerna", "Step-up al banco", "Remo sentado en polea",
        "Press de pecho sentado en máquina", "Bird dog", "Caminata inclinada en caminadora",
    ],
    ObjetivoChoice.PERDER_PESO: [
        "Caminata inclinada en caminadora", "Remo en máquina ergométrica",
        "Caminata del granjero con mancuernas", "Step-up al banco",
        "Sentadilla goblet con mancuerna", "Press de pecho sentado en máquina",
    ],
}


PARAMETROS_POR_NIVEL = {
    NivelEjercicioChoice.PRINCIPIANTE: {"series": 2, "rep_min": 10, "rep_max": 12, "rpe": 6, "tiempo": 30, "distancia": 20},
    NivelEjercicioChoice.INTERMEDIO: {"series": 3, "rep_min": 8, "rep_max": 12, "rpe": 7, "tiempo": 40, "distancia": 30},
    NivelEjercicioChoice.ENCIMA_PROMEDIO: {"series": 3, "rep_min": 8, "rep_max": 12, "rpe": 8, "tiempo": 50, "distancia": 40},
    NivelEjercicioChoice.AVANZADO: {"series": 4, "rep_min": 6, "rep_max": 10, "rpe": 8, "tiempo": 60, "distancia": 50},
}


def _cerrar_asignacion_actual(usuario):
    hoy = timezone.localdate()
    asignaciones = (
        AsignacionPlanUsuario.objects
        .select_for_update()
        .filter(usuario=usuario, estado=EstadoAsignacionChoice.ACTIVO)
    )
    for asignacion in asignaciones:
        asignacion.estado = EstadoAsignacionChoice.ABANDONADO
        asignacion.fecha_fin = max(hoy, asignacion.fecha_inicio)
        asignacion.save(update_fields=["estado", "fecha_fin", "fecha_actualizacion"])


def _crear_plan_vacio(usuario, objetivo, nivel, dias_por_semana, etiqueta):
    marca = uuid4().hex
    plan = PlanEntrenamiento.objects.create(
        nombre=f"{etiqueta} · usuario {usuario.pk} · {marca}",
        objetivo=objetivo,
        nivel=nivel,
        descripcion=(
            "Programa individual generado con el objetivo, nivel, disponibilidad "
            "y preferencias de recuperación del usuario."
        ),
        duracion_semanas=12,
        dias_por_semana=dias_por_semana,
        propietario=usuario,
        es_personalizado=True,
        activo=True,
    )
    fase = FasePlan.objects.create(
        plan=plan,
        nombre="Programa personalizado",
        orden=1,
        semana_inicio=1,
        semana_fin=12,
        descripcion="Progresión individual con técnica controlada y ajustes sostenibles.",
        activo=True,
    )
    return plan, fase


def _crear_asignacion_y_horario(usuario, plan, dias_semana):
    _cerrar_asignacion_actual(usuario)
    asignacion = AsignacionPlanUsuario.objects.create(
        usuario=usuario,
        plan=plan,
        fecha_inicio=timezone.localdate(),
    )
    HorarioPlanUsuario.objects.bulk_create([
        HorarioPlanUsuario(
            asignacion=asignacion,
            numero_dia_plan=numero,
            dia_semana=dia_semana,
            recordatorio_activo=True,
            activo=True,
        )
        for numero, dia_semana in enumerate(dias_semana, start=1)
    ])
    return asignacion


def _valores_programacion(ejercicio, nivel, descanso):
    parametros = PARAMETROS_POR_NIVEL[nivel]
    valores = {
        "series": parametros["series"],
        "descanso_segundos": descanso,
        "esfuerzo_objetivo": parametros["rpe"],
    }
    if ejercicio.tipo_medicion == TipoMedicionChoice.TIEMPO:
        valores["duracion_segundos"] = parametros["tiempo"]
    elif ejercicio.tipo_medicion == TipoMedicionChoice.DISTANCIA:
        valores["distancia_metros"] = parametros["distancia"]
    else:
        valores["repeticiones_min"] = parametros["rep_min"]
        valores["repeticiones_max"] = parametros["rep_max"]
    if ejercicio.nombre == "Caminata inclinada en caminadora":
        valores.update(series=1, duracion_segundos=600)
    elif ejercicio.nombre == "Remo en máquina ergométrica":
        valores.update(series=1, distancia_metros=1000)
    return valores


def _validar_preferencias(objetivo, nivel, dias):
    if objetivo not in ObjetivoChoice.values or nivel not in PARAMETROS_POR_NIVEL:
        raise ValidationError("Completa tu objetivo y evaluación de nivel.")
    if not 1 <= len(dias) <= 6 or len(set(dias)) != len(dias) or any(
        type(dia) is not int or dia not in range(7) for dia in dias
    ):
        raise ValidationError("Escoge entre uno y seis días distintos de la semana.")


def _segundos_estimados(valores):
    # Estimación de planificación, no un cronómetro para ejercicios por repeticiones.
    trabajo = valores.get("duracion_segundos")
    if trabajo is None:
        trabajo = float(valores.get("distancia_metros", 0)) * 0.5
    if not trabajo:
        trabajo = valores.get("repeticiones_max", 12) * 4
    return valores["series"] * trabajo + max(0, valores["series"] - 1) * valores["descanso_segundos"] + 90


@transaction.atomic
def crear_rutina_automatica(usuario, objetivo, nivel, dias_semana, minutos, descanso, minutos_por_dia=None):
    _validar_preferencias(objetivo, nivel, dias_semana)
    minutos_por_dia = minutos_por_dia or {}
    presupuestos = [minutos_por_dia.get(str(dia), minutos) for dia in dias_semana]
    if any(type(valor) is not int or valor < 45 for valor in presupuestos):
        raise ValidationError("Cada entrenamiento debe durar al menos 45 minutos.")
    if not 15 <= descanso <= 1800:
        raise ValidationError("El descanso debe estar entre 15 y 1800 segundos.")

    plan, fase = _crear_plan_vacio(
        usuario, objetivo, nivel, len(dias_semana), "Rutina MaikerGym",
    )
    niveles = list(PARAMETROS_POR_NIVEL)
    ejercicios = {
        ejercicio.nombre: ejercicio
        for ejercicio in Ejercicio.objects.filter(activo=True, nivel__in=niveles[:niveles.index(nivel) + 1])
    }
    enfoques = ENFOQUES_POR_CANTIDAD[len(dias_semana)]
    prioridad = PRIORIDAD_POR_OBJETIVO.get(objetivo, [])

    for indice, enfoque in enumerate(enfoques, start=1):
        minutos_dia = presupuestos[indice - 1]
        dia = DiaPlan.objects.create(
            fase=fase,
            numero=indice,
            nombre=NOMBRES_ENFOQUE[enfoque],
            enfoque=NOMBRES_ENFOQUE[enfoque],
            descripcion=f"Disponibilidad: {minutos_dia} minutos.",
            activo=True,
        )
        nombres_base = list(EJERCICIOS_POR_ENFOQUE[enfoque])
        sustitutos = {
            "Sentadilla con barra": "Sentadilla goblet con mancuerna",
            "Peso muerto rumano con barra": "Puente de glúteos en suelo",
            "Hip thrust con barra": "Puente de glúteos en suelo",
            "Press de banca con barra": "Press de pecho sentado en máquina",
            "Press militar sentado con mancuernas": "Elevaciones laterales con mancuernas",
        }
        nombres_base = list(dict.fromkeys(
            nombre if nombre in ejercicios else sustitutos.get(nombre, nombre)
            for nombre in nombres_base
        ))
        candidatos = [nombre for nombre in prioridad if nombre in nombres_base]
        candidatos.extend(nombre for nombre in nombres_base if nombre not in candidatos)
        disponibles = [ejercicios[nombre] for nombre in candidatos if nombre in ejercicios]
        if not disponibles:
            raise ValidationError(
                "El catálogo de ejercicios todavía no está listo para generar esta sesión."
            )
        # Reservar calentamiento/transiciones; no añadir volumen ilimitado por disponer de más tiempo.
        segundos = 10 * 60
        seleccion = []
        limite = 6 if nivel == NivelEjercicioChoice.PRINCIPIANTE else 8
        for ejercicio in disponibles:
            valores = _valores_programacion(ejercicio, nivel, descanso)
            coste = _segundos_estimados(valores)
            if segundos + coste <= minutos_dia * 60 and len(seleccion) < limite:
                seleccion.append((ejercicio, valores))
                segundos += coste
        if len(seleccion) < min(3, len(disponibles)):
            raise ValidationError("El descanso elegido no cabe con una sesión equilibrada. Aumenta el tiempo disponible o reduce el descanso.")
        dia.descripcion += f" Duración orientativa: {int((segundos + 59) // 60)} min, con descansos y 10 min de preparación. No es obligatorio agotar el tiempo disponible."
        dia.save(update_fields=["descripcion"])
        for orden, (ejercicio, valores) in enumerate(seleccion, start=1):
            EjercicioProgramado.objects.create(
                dia=dia,
                ejercicio=ejercicio,
                orden=orden,
                notas="Prioriza una ejecución estable y detén la serie si aparece dolor.",
                activo=True,
                **valores,
            )

    return _crear_asignacion_y_horario(usuario, plan, dias_semana)


@transaction.atomic
def crear_rutina_personalizada(usuario, objetivo, nivel, dias_semana, filas):
    _validar_preferencias(objetivo, nivel, dias_semana)
    if not 1 <= len(dias_semana) <= 6:
        raise ValidationError("Escoge entre uno y seis días para entrenar.")
    if not filas:
        raise ValidationError("Agrega al menos un ejercicio a tu rutina.")

    plan, fase = _crear_plan_vacio(
        usuario, objetivo, nivel, len(dias_semana), "Rutina creada por el usuario",
    )
    dias = {}
    for numero, dia_semana in enumerate(dias_semana, start=1):
        dias[numero] = DiaPlan.objects.create(
            fase=fase,
            numero=numero,
            nombre=f"Sesión {numero}",
            enfoque="Selección personal",
            descripcion="Rutina configurada directamente por el usuario.",
            activo=True,
        )

    usados = set()
    ordenes = {numero: 0 for numero in dias}
    for fila in filas:
        numero_dia = int(fila["dia"])
        ejercicio = Ejercicio.objects.get(pk=int(fila["ejercicio_id"]), activo=True)
        clave = (numero_dia, ejercicio.pk)
        if numero_dia not in dias or clave in usados:
            raise ValidationError("Revisa los días y elimina los ejercicios repetidos dentro de una misma sesión.")
        usados.add(clave)
        ordenes[numero_dia] += 1
        cantidad = max(1, int(fila["cantidad"]))
        series = min(20, max(1, int(fila["series"])))
        descanso = min(1800, max(15, int(fila["descanso"])))
        valores = {
            "series": series,
            "descanso_segundos": descanso,
            "esfuerzo_objetivo": 7,
        }
        if ejercicio.tipo_medicion == TipoMedicionChoice.TIEMPO:
            valores["duracion_segundos"] = cantidad
        elif ejercicio.tipo_medicion == TipoMedicionChoice.DISTANCIA:
            valores["distancia_metros"] = cantidad
        else:
            valores["repeticiones_min"] = cantidad
            valores["repeticiones_max"] = cantidad
        programado = EjercicioProgramado(
            dia=dias[numero_dia],
            ejercicio=ejercicio,
            orden=ordenes[numero_dia],
            notas=(
                "Rutina diseñada por el usuario. Ajusta o detén el ejercicio ante dolor, "
                "mareo o pérdida de técnica."
            ),
            activo=True,
            **valores,
        )
        programado.full_clean()
        programado.save()

    dias_vacios = [numero for numero, total in ordenes.items() if total == 0]
    if dias_vacios:
        raise ValidationError("Cada día seleccionado necesita al menos un ejercicio.")

    return _crear_asignacion_y_horario(usuario, plan, dias_semana)


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


@transaction.atomic
def iniciar_serie_entrenamiento(usuario, serie_id):
    try:
        serie_objetivo = (
            SerieEjercicioSesion.objects
            .select_related(
                "ejercicio_sesion__sesion__asignacion",
            )
            .get(pk=serie_id)
        )
    except SerieEjercicioSesion.DoesNotExist as error:
        raise ValidationError(
            "La serie seleccionada no existe."
        ) from error

    sesion = (
        SesionEntrenamiento.objects
        .select_for_update()
        .select_related("asignacion")
        .get(pk=serie_objetivo.ejercicio_sesion.sesion_id)
    )

    if sesion.asignacion.usuario_id != usuario.id:
        raise ValidationError(
            "No tienes permiso para usar esta serie."
        )

    if sesion.estado == EstadoSesionChoice.COMPLETADA:
        raise ValidationError(
            "Este entrenamiento ya fue completado."
        )

    series_sesion = list(
        SerieEjercicioSesion.objects
        .select_for_update()
        .filter(
            ejercicio_sesion__sesion_id=sesion.pk,
        )
        .select_related(
            "ejercicio_sesion__ejercicio_programado__ejercicio",
        )
        .order_by(
            "ejercicio_sesion__ejercicio_programado__orden",
            "numero",
        )
    )

    serie = next(
        (
            item
            for item in series_sesion
            if item.pk == serie_objetivo.pk
        ),
        None,
    )

    if serie is None:
        raise ValidationError(
            "La serie no pertenece a este entrenamiento."
        )

    otra_serie_activa = next(
        (
            item
            for item in series_sesion
            if (
                item.estado == EstadoSerieChoice.EN_PROGRESO
                and item.pk != serie.pk
            )
        ),
        None,
    )

    if otra_serie_activa is not None:
        raise ValidationError(
            "Ya existe otra serie en progreso."
        )

    if serie.estado == EstadoSerieChoice.COMPLETADA:
        raise ValidationError(
            "Esta serie ya fue completada."
        )

    if serie.estado == EstadoSerieChoice.EN_PROGRESO:
        return serie, False

    serie_actual = next(
        (
            item
            for item in series_sesion
            if item.estado != EstadoSerieChoice.COMPLETADA
        ),
        None,
    )

    if serie_actual is None or serie_actual.pk != serie.pk:
        raise ValidationError(
            "Debes completar primero la serie indicada."
        )

    ahora = timezone.now()
    ultima_completada = next(
        (
            item
            for item in reversed(series_sesion)
            if item.estado == EstadoSerieChoice.COMPLETADA
        ),
        None,
    )

    if (
        ultima_completada is not None
        and ultima_completada.descanso_hasta is not None
        and not ultima_completada.descanso_omitido
        and ultima_completada.descanso_hasta > ahora
    ):
        segundos_restantes = (
            int(
                (
                    ultima_completada.descanso_hasta - ahora
                ).total_seconds()
            )
            + 1
        )
        raise ValidationError(
            f"Aún quedan {segundos_restantes} segundos "
            "de descanso."
        )

    serie.estado = EstadoSerieChoice.EN_PROGRESO
    serie.fecha_inicio = ahora
    serie.fecha_finalizacion = None
    serie.descanso_hasta = None
    serie.descanso_omitido = False
    serie.full_clean()
    serie.save(
        update_fields=[
            "estado",
            "fecha_inicio",
            "fecha_finalizacion",
            "descanso_hasta",
            "descanso_omitido",
            "fecha_actualizacion",
        ]
    )

    campos_sesion = []

    if sesion.estado == EstadoSesionChoice.PENDIENTE:
        sesion.estado = EstadoSesionChoice.EN_PROGRESO
        campos_sesion.append("estado")

    if sesion.fecha_inicio is None:
        sesion.fecha_inicio = ahora
        campos_sesion.append("fecha_inicio")

    if campos_sesion:
        campos_sesion.append("fecha_actualizacion")
        sesion.save(update_fields=campos_sesion)

    return serie, True


@transaction.atomic
def completar_serie_entrenamiento(
    usuario,
    serie_id,
    repeticiones_realizadas=None,
    duracion_realizada_segundos=None,
    distancia_realizada_metros=None,
    peso_utilizado_kg=None,
):
    try:
        serie = (
            SerieEjercicioSesion.objects
            .select_for_update()
            .select_related(
                "ejercicio_sesion__sesion__asignacion",
                "ejercicio_sesion__ejercicio_programado__ejercicio",
            )
            .get(pk=serie_id)
        )
    except SerieEjercicioSesion.DoesNotExist as error:
        raise ValidationError(
            "La serie seleccionada no existe."
        ) from error

    registro = serie.ejercicio_sesion
    sesion = registro.sesion
    programado = registro.ejercicio_programado
    ejercicio = programado.ejercicio

    if sesion.asignacion.usuario_id != usuario.id:
        raise ValidationError(
            "No tienes permiso para completar esta serie."
        )

    if serie.estado == EstadoSerieChoice.COMPLETADA:
        return serie, False, registro, sesion

    if serie.estado != EstadoSerieChoice.EN_PROGRESO:
        raise ValidationError(
            "Debes comenzar la serie antes de finalizarla."
        )

    repeticiones = None
    duracion = None
    distancia = None

    if ejercicio.tipo_medicion == TipoMedicionChoice.REPETICIONES:
        repeticiones = _convertir_entero(
            repeticiones_realizadas,
            "las repeticiones de la serie",
            requerido=True,
        )

        if (
            programado.repeticiones_min is not None
            and repeticiones < programado.repeticiones_min
        ):
            raise ValidationError(
                "Debes realizar al menos "
                f"{programado.repeticiones_min} repeticiones."
            )

    elif ejercicio.tipo_medicion == TipoMedicionChoice.TIEMPO:
        duracion = _convertir_entero(
            duracion_realizada_segundos,
            "la duración de la serie en segundos",
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
            "la distancia de la serie en metros",
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

    ahora = timezone.now()
    serie.estado = EstadoSerieChoice.COMPLETADA
    serie.repeticiones_realizadas = repeticiones
    serie.duracion_realizada_segundos = duracion
    serie.distancia_realizada_metros = distancia
    serie.peso_utilizado_kg = peso
    serie.fecha_finalizacion = ahora
    serie.descanso_hasta = ahora + timedelta(
        seconds=programado.descanso_segundos
    )
    serie.descanso_omitido = False
    serie.full_clean()
    serie.save(
        update_fields=[
            "estado",
            "repeticiones_realizadas",
            "duracion_realizada_segundos",
            "distancia_realizada_metros",
            "peso_utilizado_kg",
            "fecha_finalizacion",
            "descanso_hasta",
            "descanso_omitido",
            "fecha_actualizacion",
        ]
    )

    series_completadas = registro.series.filter(
        estado=EstadoSerieChoice.COMPLETADA
    )
    resumen = series_completadas.aggregate(
        repeticiones=Sum("repeticiones_realizadas"),
        duracion=Sum("duracion_realizada_segundos"),
        distancia=Sum("distancia_realizada_metros"),
        peso=Max("peso_utilizado_kg"),
    )
    cantidad_completada = series_completadas.count()

    registro.series_completadas = cantidad_completada
    registro.repeticiones_realizadas = resumen["repeticiones"]
    registro.duracion_realizada_segundos = resumen["duracion"]
    registro.distancia_realizada_metros = resumen["distancia"]
    registro.peso_utilizado_kg = resumen["peso"]
    registro.save(
        update_fields=[
            "series_completadas",
            "repeticiones_realizadas",
            "duracion_realizada_segundos",
            "distancia_realizada_metros",
            "peso_utilizado_kg",
            "fecha_actualizacion",
        ]
    )

    if cantidad_completada >= programado.series:
        registro, _, sesion = completar_ejercicio_sesion(
            usuario=usuario,
            ejercicio_sesion_id=registro.pk,
            series_completadas=cantidad_completada,
            repeticiones_realizadas=resumen["repeticiones"],
            duracion_realizada_segundos=resumen["duracion"],
            distancia_realizada_metros=resumen["distancia"],
            peso_utilizado_kg=resumen["peso"],
        )

    return serie, True, registro, sesion


@transaction.atomic
def omitir_descanso_serie(usuario, serie_id):
    try:
        serie = (
            SerieEjercicioSesion.objects
            .select_for_update()
            .select_related(
                "ejercicio_sesion__sesion__asignacion",
            )
            .get(pk=serie_id)
        )
    except SerieEjercicioSesion.DoesNotExist as error:
        raise ValidationError(
            "La serie seleccionada no existe."
        ) from error

    sesion = serie.ejercicio_sesion.sesion

    if sesion.asignacion.usuario_id != usuario.id:
        raise ValidationError(
            "No tienes permiso para modificar este descanso."
        )

    if serie.estado != EstadoSerieChoice.COMPLETADA:
        raise ValidationError(
            "Solo puedes omitir el descanso de una serie completada."
        )

    ultima_completada = (
        SerieEjercicioSesion.objects
        .select_for_update()
        .filter(
            ejercicio_sesion__sesion_id=sesion.pk,
            estado=EstadoSerieChoice.COMPLETADA,
        )
        .order_by(
            "-fecha_finalizacion",
            "-pk",
        )
        .first()
    )

    if ultima_completada is None or ultima_completada.pk != serie.pk:
        raise ValidationError(
            "Solo puedes omitir el descanso de la última serie."
        )

    if serie.descanso_omitido:
        return serie, False

    if (
        serie.descanso_hasta is None
        or serie.descanso_hasta <= timezone.now()
    ):
        return serie, False

    serie.descanso_omitido = True
    serie.save(
        update_fields=[
            "descanso_omitido",
            "fecha_actualizacion",
        ]
    )

    return serie, True
