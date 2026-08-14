from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from gym_project.gym_app.models import (
    DiaPlan,
    Ejercicio,
    EjercicioProgramado,
    FasePlan,
    NivelEjercicioChoice,
    ObjetivoChoice,
    PlanEntrenamiento,
)


FASES = [
    {
        "orden": 1,
        "nombre": "Adaptación técnica",
        "semana_inicio": 1,
        "semana_fin": 4,
        "descripcion": (
            "Primera fase para aprender la técnica, controlar los "
            "movimientos y preparar el cuerpo para aumentar el volumen."
        ),
        "activo": True,
    },
    {
        "orden": 2,
        "nombre": "Progresión de volumen",
        "semana_inicio": 5,
        "semana_fin": 8,
        "descripcion": (
            "Segunda fase con más series y mayor esfuerzo para estimular "
            "el crecimiento muscular de manera progresiva."
        ),
        "activo": True,
    },
    {
        "orden": 3,
        "nombre": "Intensificación",
        "semana_inicio": 9,
        "semana_fin": 12,
        "descripcion": (
            "Tercera fase con ejercicios más exigentes, descansos "
            "ajustados y un esfuerzo objetivo superior."
        ),
        "activo": True,
    },
]

DIAS = [
    {
        "numero": 1,
        "nombre": "Piernas y glúteos",
        "enfoque": (
            "Cuádriceps, femorales, glúteos y pantorrillas"
        ),
        "descripcion": (
            "Entrenamiento de tren inferior con ejercicios compuestos "
            "y movimientos de aislamiento."
        ),
        "activo": True,
    },
    {
        "numero": 2,
        "nombre": "Pecho, hombros y tríceps",
        "enfoque": (
            "Pecho, hombros y tríceps"
        ),
        "descripcion": (
            "Entrenamiento de empuje para desarrollar el tren superior."
        ),
        "activo": True,
    },
    {
        "numero": 3,
        "nombre": "Espalda, bíceps y abdomen",
        "enfoque": (
            "Espalda, bíceps, antebrazos y abdomen"
        ),
        "descripcion": (
            "Entrenamiento de tracción complementado con trabajo "
            "de estabilidad abdominal."
        ),
        "activo": True,
    },
]

def ejercicio_por_repeticiones(
    nombre,
    orden,
    series,
    repeticiones_min,
    repeticiones_max,
    descanso,
    obligatorio=True,
    esfuerzo=6,
):
    return {
        "ejercicio": nombre,
        "orden": orden,
        "series": series,
        "repeticiones_min": repeticiones_min,
        "repeticiones_max": repeticiones_max,
        "duracion_segundos": None,
        "distancia_metros": None,
        "descanso_segundos": descanso,
        "esfuerzo_objetivo": esfuerzo,
        "obligatorio": obligatorio,
        "notas": "",
        "activo": True,
    }
def ejercicio_por_tiempo(
    nombre,
    orden,
    series,
    duracion_segundos,
    descanso,
    obligatorio=True,
    esfuerzo=6,
):
    return {
        "ejercicio": nombre,
        "orden": orden,
        "series": series,
        "repeticiones_min": None,
        "repeticiones_max": None,
        "duracion_segundos": duracion_segundos,
        "distancia_metros": None,
        "descanso_segundos": descanso,
        "esfuerzo_objetivo": esfuerzo,
        "obligatorio": obligatorio,
        "notas": "",
        "activo": True,
    }

PROGRAMACION = {
    1: {
        1: [
            ejercicio_por_repeticiones(
                "Sentadilla con barra",
                orden=1,
                series=3,
                repeticiones_min=10,
                repeticiones_max=12,
                descanso=90,
            ),
            ejercicio_por_repeticiones(
                "Peso muerto rumano con barra",
                orden=2,
                series=3,
                repeticiones_min=10,
                repeticiones_max=12,
                descanso=90,
            ),
            ejercicio_por_repeticiones(
                "Prensa de piernas en máquina",
                orden=3,
                series=3,
                repeticiones_min=12,
                repeticiones_max=15,
                descanso=75,
            ),
            ejercicio_por_repeticiones(
                "Curl femoral tumbado en máquina",
                orden=4,
                series=2,
                repeticiones_min=12,
                repeticiones_max=15,
                descanso=60,
            ),
            ejercicio_por_repeticiones(
                "Hip thrust con barra",
                orden=5,
                series=3,
                repeticiones_min=10,
                repeticiones_max=12,
                descanso=75,
            ),
            ejercicio_por_repeticiones(
                "Elevación de talones de pie en máquina",
                orden=6,
                series=3,
                repeticiones_min=15,
                repeticiones_max=20,
                descanso=45,
                obligatorio=False,
            ),
        ],
                2: [
            ejercicio_por_repeticiones(
                "Press de banca con barra",
                orden=1,
                series=3,
                repeticiones_min=10,
                repeticiones_max=12,
                descanso=90,
            ),
            ejercicio_por_repeticiones(
                "Press inclinado con mancuernas",
                orden=2,
                series=3,
                repeticiones_min=10,
                repeticiones_max=12,
                descanso=75,
            ),
            ejercicio_por_repeticiones(
                "Aperturas de pecho en máquina",
                orden=3,
                series=2,
                repeticiones_min=12,
                repeticiones_max=15,
                descanso=60,
            ),
            ejercicio_por_repeticiones(
                "Press militar sentado con mancuernas",
                orden=4,
                series=2,
                repeticiones_min=10,
                repeticiones_max=12,
                descanso=75,
            ),
            ejercicio_por_repeticiones(
                "Extensión de tríceps en polea",
                orden=5,
                series=2,
                repeticiones_min=12,
                repeticiones_max=15,
                descanso=60,
            ),
            ejercicio_por_repeticiones(
                "Elevaciones laterales con mancuernas",
                orden=6,
                series=2,
                repeticiones_min=12,
                repeticiones_max=15,
                descanso=45,
                obligatorio=False,
            ),
        ],
        3: [
            ejercicio_por_repeticiones(
                "Jalón al pecho en polea",
                orden=1,
                series=3,
                repeticiones_min=10,
                repeticiones_max=12,
                descanso=75,
            ),
            ejercicio_por_repeticiones(
                "Remo sentado en polea",
                orden=2,
                series=3,
                repeticiones_min=10,
                repeticiones_max=12,
                descanso=75,
            ),
            ejercicio_por_repeticiones(
                "Dominadas asistidas en máquina",
                orden=3,
                series=2,
                repeticiones_min=8,
                repeticiones_max=10,
                descanso=90,
            ),
            ejercicio_por_repeticiones(
                "Curl de bíceps con barra Z",
                orden=4,
                series=2,
                repeticiones_min=10,
                repeticiones_max=12,
                descanso=60,
            ),
            ejercicio_por_tiempo(
                "Plancha frontal sobre antebrazos",
                orden=5,
                series=3,
                duracion_segundos=20,
                descanso=45,
            ),
            ejercicio_por_repeticiones(
                "Curl martillo con mancuernas",
                orden=6,
                series=2,
                repeticiones_min=10,
                repeticiones_max=12,
                descanso=60,
                obligatorio=False,
            ),
        ],
    },
}
def aumentar_volumen(ejercicios):
    ejercicios_progresados = []

    for datos in ejercicios:
        progresado = datos.copy()

        progresado["series"] = min(
            progresado["series"] + 1,
            4,
        )
        progresado["esfuerzo_objetivo"] = 7
        progresado["descanso_segundos"] = min(
            progresado["descanso_segundos"] + 15,
            120,
        )

        if progresado["repeticiones_min"] is not None:
            nuevas_minimas = max(
                progresado["repeticiones_min"] - 2,
                8,
            )
            nuevas_maximas = max(
                progresado["repeticiones_max"] - 2,
                nuevas_minimas,
            )

            progresado["repeticiones_min"] = nuevas_minimas
            progresado["repeticiones_max"] = nuevas_maximas

        if progresado["duracion_segundos"] is not None:
            progresado["duracion_segundos"] += 10

        progresado["notas"] = (
            "Fase de progresión. Aumenta la carga solamente si "
            "completas el rango manteniendo una técnica correcta."
        )

        ejercicios_progresados.append(progresado)

    return ejercicios_progresados


PROGRAMACION[2] = {
    numero_dia: aumentar_volumen(ejercicios)
    for numero_dia, ejercicios in PROGRAMACION[1].items()
}
def aumentar_intensidad(ejercicios):
    ejercicios_intensificados = []

    for datos in ejercicios:
        intensificado = datos.copy()

        intensificado["esfuerzo_objetivo"] = 8
        intensificado["descanso_segundos"] = min(
            intensificado["descanso_segundos"] + 15,
            150,
        )

        if intensificado["repeticiones_min"] is not None:
            nuevas_minimas = max(
                intensificado["repeticiones_min"] - 2,
                6,
            )
            nuevas_maximas = max(
                intensificado["repeticiones_max"] - 2,
                nuevas_minimas,
            )

            intensificado["repeticiones_min"] = nuevas_minimas
            intensificado["repeticiones_max"] = nuevas_maximas

        if intensificado["duracion_segundos"] is not None:
            intensificado["duracion_segundos"] += 10

        intensificado["notas"] = (
            "Fase de intensificación. Utiliza una carga mayor únicamente "
            "si puedes mantener la técnica y completar el rango indicado."
        )

        ejercicios_intensificados.append(intensificado)

    return ejercicios_intensificados


PROGRAMACION[3] = {
    numero_dia: aumentar_intensidad(ejercicios)
    for numero_dia, ejercicios in PROGRAMACION[2].items()
}
class Command(BaseCommand):
    help = "Carga el plan inicial de hipertrofia de MaikerGym."

    @transaction.atomic
    def handle(self, *args, **options):
        plan, plan_creado = PlanEntrenamiento.objects.update_or_create(
            nombre="Hipertrofia inicial de 12 semanas",
            defaults={
                "objetivo": ObjetivoChoice.HIPERTROFIA,
                "nivel": NivelEjercicioChoice.PRINCIPIANTE,
                "descripcion": (
                    "Plan progresivo de tres días semanales para aprender "
                    "los ejercicios principales, aumentar el volumen de "
                    "entrenamiento y desarrollar masa muscular."
                ),
                "duracion_semanas": 12,
                "dias_por_semana": 3,
                "activo": True,
            },
        )

        fases_creadas = 0
        fases_actualizadas = 0
        dias_creados = 0
        dias_actualizados = 0
        programados_creados = 0
        programados_actualizados = 0

        for datos in FASES:
            valores = datos.copy()
            orden = valores.pop("orden")

            fase, fase_creada = FasePlan.objects.update_or_create(
                plan=plan,
                orden=orden,
                defaults=valores,
            )

            if fase_creada:
                fases_creadas += 1
            else:
                fases_actualizadas += 1

            self.stdout.write(
                f"Procesada: {fase.nombre} "
                f"(semanas {fase.semana_inicio}-{fase.semana_fin})"
            )

            for datos_dia in DIAS:
                valores_dia = datos_dia.copy()
                numero_dia = valores_dia.pop("numero")

                dia, dia_creado = DiaPlan.objects.update_or_create(
                    fase=fase,
                    numero=numero_dia,
                    defaults=valores_dia,
                )

                if dia_creado:
                    dias_creados += 1
                else:
                    dias_actualizados += 1

                self.stdout.write(
                    f"  Día {dia.numero}: {dia.nombre}"
                )

                ejercicios_del_dia = PROGRAMACION.get(
                    fase.orden,
                    {},
                ).get(numero_dia, [])

                for datos_programados in ejercicios_del_dia:
                    valores_programados = datos_programados.copy()
                    nombre_ejercicio = valores_programados.pop(
                        "ejercicio"
                    )

                    ejercicio = Ejercicio.objects.filter(
                        nombre=nombre_ejercicio
                    ).first()

                    if ejercicio is None:
                        raise CommandError(
                            "No existe el ejercicio: "
                            f"{nombre_ejercicio}. "
                            "Ejecuta primero cargar_ejercicios."
                        )

                    programado, programado_creado = (
                        EjercicioProgramado.objects.update_or_create(
                            dia=dia,
                            ejercicio=ejercicio,
                            defaults=valores_programados,
                        )
                    )

                    if programado_creado:
                        programados_creados += 1
                    else:
                        programados_actualizados += 1

                    self.stdout.write(
                        f"    {programado.orden}. "
                        f"{programado.ejercicio.nombre}"
                    )

        estado_plan = "creado" if plan_creado else "actualizado"

        self.stdout.write(
            self.style.SUCCESS(
                f"Plan {estado_plan}: {plan.nombre}. "
                f"Fases creadas: {fases_creadas}. "
                f"Fases actualizadas: {fases_actualizadas}. "
                f"Días creados: {dias_creados}. "
                f"Días actualizados: {dias_actualizados}. "
                f"Ejercicios creados: {programados_creados}. "
                f"Ejercicios actualizados: "
                f"{programados_actualizados}."
            )
        )