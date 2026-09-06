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


def ejercicio_por_distancia(
    nombre,
    orden,
    series,
    distancia_metros,
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
        "duracion_segundos": None,
        "distancia_metros": distancia_metros,
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

        if progresado["distancia_metros"] is not None:
            progresado["distancia_metros"] = round(
                progresado["distancia_metros"] * 1.15,
            )

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

        if intensificado["distancia_metros"] is not None:
            intensificado["distancia_metros"] = round(
                intensificado["distancia_metros"] * 1.10,
            )

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


def construir_programacion(base):
    volumen = {
        numero_dia: aumentar_volumen(ejercicios)
        for numero_dia, ejercicios in base.items()
    }
    intensidad = {
        numero_dia: aumentar_intensidad(ejercicios)
        for numero_dia, ejercicios in volumen.items()
    }
    return {1: base, 2: volumen, 3: intensidad}


def progresar_perdida_peso(ejercicios, fase):
    progresados = []
    incremento_repeticiones = 2 if fase == 2 else 4
    factor_cardio = 1.15 if fase == 2 else 1.30
    reduccion_descanso = 10 if fase == 2 else 15

    for datos in ejercicios:
        progresado = datos.copy()
        progresado["series"] = min(progresado["series"] + 1, 4)
        progresado["esfuerzo_objetivo"] = 6 if fase == 2 else 7
        progresado["descanso_segundos"] = max(
            progresado["descanso_segundos"] - reduccion_descanso,
            30,
        )

        if progresado["repeticiones_min"] is not None:
            progresado["repeticiones_min"] += incremento_repeticiones
            progresado["repeticiones_max"] = min(
                progresado["repeticiones_max"]
                + incremento_repeticiones,
                20,
            )

        if progresado["duracion_segundos"] is not None:
            progresado["duracion_segundos"] = round(
                progresado["duracion_segundos"] * factor_cardio,
            )

        if progresado["distancia_metros"] is not None:
            progresado["distancia_metros"] = round(
                progresado["distancia_metros"] * factor_cardio,
            )

        progresado["notas"] = (
            "Progresa solamente si completas el trabajo con respiración "
            "controlada y técnica estable. Detente ante dolor, mareo o "
            "dificultad respiratoria fuera de lo habitual."
        )
        progresados.append(progresado)

    return progresados


def construir_programacion_perdida_peso(base):
    return {
        1: base,
        2: {
            numero_dia: progresar_perdida_peso(ejercicios, 2)
            for numero_dia, ejercicios in base.items()
        },
        3: {
            numero_dia: progresar_perdida_peso(ejercicios, 3)
            for numero_dia, ejercicios in base.items()
        },
    }


PROGRAMACION_ESTETICA = construir_programacion({
    1: [
        ejercicio_por_repeticiones(
            "Sentadilla goblet con mancuerna", 1, 3, 10, 12, 75,
        ),
        ejercicio_por_repeticiones(
            "Zancada estática con mancuernas", 2, 3, 10, 12, 75,
        ),
        ejercicio_por_repeticiones(
            "Hip thrust con barra", 3, 3, 10, 12, 75,
        ),
        ejercicio_por_repeticiones(
            "Step-up al banco", 4, 2, 10, 12, 60,
        ),
        ejercicio_por_repeticiones(
            "Abducción de cadera en máquina", 5, 2, 15, 20, 45,
        ),
        ejercicio_por_repeticiones(
            "Elevación de talones de pie en máquina",
            6, 3, 15, 20, 45, obligatorio=False,
        ),
    ],
    2: [
        ejercicio_por_repeticiones(
            "Press de pecho sentado en máquina", 1, 3, 10, 12, 75,
        ),
        ejercicio_por_repeticiones(
            "Press inclinado con mancuernas", 2, 3, 10, 12, 75,
        ),
        ejercicio_por_repeticiones(
            "Jalón al pecho en polea", 3, 3, 10, 12, 75,
        ),
        ejercicio_por_repeticiones(
            "Face pull en polea", 4, 2, 12, 15, 60,
        ),
        ejercicio_por_repeticiones(
            "Elevaciones laterales con mancuernas", 5, 2, 12, 15, 45,
        ),
        ejercicio_por_repeticiones(
            "Extensión de tríceps sobre la cabeza en polea",
            6, 2, 10, 15, 60, obligatorio=False,
        ),
    ],
    3: [
        ejercicio_por_repeticiones(
            "Peso muerto rumano con barra", 1, 3, 10, 12, 90,
        ),
        ejercicio_por_repeticiones(
            "Remo sentado en polea", 2, 3, 10, 12, 75,
        ),
        ejercicio_por_repeticiones(
            "Curl de bíceps en polea baja", 3, 2, 10, 15, 60,
        ),
        ejercicio_por_repeticiones(
            "Press Pallof en polea", 4, 3, 10, 12, 45,
        ),
        ejercicio_por_repeticiones(
            "Bird dog", 5, 3, 8, 10, 45,
        ),
        ejercicio_por_tiempo(
            "Caminata inclinada en caminadora",
            6, 1, 600, 60, obligatorio=False, esfuerzo=5,
        ),
    ],
})


PROGRAMACION_SALUD = construir_programacion({
    1: [
        ejercicio_por_repeticiones(
            "Sentadilla goblet con mancuerna", 1, 2, 10, 12, 75,
            esfuerzo=5,
        ),
        ejercicio_por_repeticiones(
            "Step-up al banco", 2, 2, 8, 10, 60, esfuerzo=5,
        ),
        ejercicio_por_repeticiones(
            "Puente de glúteos en suelo", 3, 3, 12, 15, 60,
            esfuerzo=5,
        ),
        ejercicio_por_repeticiones(
            "Abducción de cadera en máquina", 4, 2, 12, 15, 45,
            esfuerzo=5,
        ),
        ejercicio_por_repeticiones(
            "Elevación de talones de pie en máquina", 5, 2, 12, 15, 45,
            esfuerzo=5,
        ),
        ejercicio_por_tiempo(
            "Caminata inclinada en caminadora",
            6, 1, 480, 60, obligatorio=False, esfuerzo=4,
        ),
    ],
    2: [
        ejercicio_por_repeticiones(
            "Press de pecho sentado en máquina", 1, 2, 10, 12, 60,
            esfuerzo=5,
        ),
        ejercicio_por_repeticiones(
            "Remo sentado en polea", 2, 2, 10, 12, 60, esfuerzo=5,
        ),
        ejercicio_por_repeticiones(
            "Jalón al pecho en polea", 3, 2, 10, 12, 60, esfuerzo=5,
        ),
        ejercicio_por_repeticiones(
            "Face pull en polea", 4, 2, 12, 15, 45, esfuerzo=5,
        ),
        ejercicio_por_repeticiones(
            "Curl de bíceps en polea baja", 5, 2, 10, 12, 45,
            obligatorio=False, esfuerzo=5,
        ),
        ejercicio_por_repeticiones(
            "Extensión de tríceps en polea", 6, 2, 10, 12, 45,
            obligatorio=False, esfuerzo=5,
        ),
    ],
    3: [
        ejercicio_por_repeticiones(
            "Bird dog", 1, 3, 8, 10, 45, esfuerzo=4,
        ),
        ejercicio_por_repeticiones(
            "Press Pallof en polea", 2, 3, 10, 12, 45, esfuerzo=5,
        ),
        ejercicio_por_repeticiones(
            "Puente de glúteos en suelo", 3, 2, 12, 15, 45,
            esfuerzo=5,
        ),
        ejercicio_por_repeticiones(
            "Caminata del granjero con mancuernas", 4, 3, 20, 30, 60,
            esfuerzo=5,
        ),
        ejercicio_por_repeticiones(
            "Zancada estática con mancuernas", 5, 2, 8, 10, 60,
            obligatorio=False, esfuerzo=5,
        ),
        ejercicio_por_tiempo(
            "Plancha frontal sobre antebrazos", 6, 2, 20, 45,
            obligatorio=False, esfuerzo=5,
        ),
    ],
})


PROGRAMACION_PERDER_PESO = construir_programacion_perdida_peso({
    1: [
        ejercicio_por_repeticiones(
            "Sentadilla goblet con mancuerna", 1, 3, 12, 15, 60,
            esfuerzo=5,
        ),
        ejercicio_por_repeticiones(
            "Zancada estática con mancuernas", 2, 2, 10, 12, 60,
            esfuerzo=5,
        ),
        ejercicio_por_repeticiones(
            "Step-up al banco", 3, 2, 10, 12, 60, esfuerzo=5,
        ),
        ejercicio_por_repeticiones(
            "Puente de glúteos en suelo", 4, 3, 12, 15, 45,
            esfuerzo=5,
        ),
        ejercicio_por_repeticiones(
            "Elevación de talones de pie en máquina", 5, 2, 15, 20, 45,
            obligatorio=False, esfuerzo=5,
        ),
        ejercicio_por_tiempo(
            "Caminata inclinada en caminadora", 6, 1, 600, 45,
            esfuerzo=5,
        ),
    ],
    2: [
        ejercicio_por_repeticiones(
            "Press de pecho sentado en máquina", 1, 3, 10, 12, 60,
            esfuerzo=5,
        ),
        ejercicio_por_repeticiones(
            "Jalón al pecho en polea", 2, 3, 10, 12, 60,
            esfuerzo=5,
        ),
        ejercicio_por_repeticiones(
            "Remo sentado en polea", 3, 3, 10, 12, 60,
            esfuerzo=5,
        ),
        ejercicio_por_repeticiones(
            "Face pull en polea", 4, 2, 12, 15, 45, esfuerzo=5,
        ),
        ejercicio_por_repeticiones(
            "Curl de bíceps en polea baja", 5, 2, 10, 12, 45,
            obligatorio=False, esfuerzo=5,
        ),
        ejercicio_por_repeticiones(
            "Extensión de tríceps sobre la cabeza en polea",
            6, 2, 10, 12, 45, obligatorio=False, esfuerzo=5,
        ),
    ],
    3: [
        ejercicio_por_repeticiones(
            "Peso muerto rumano con barra", 1, 3, 10, 12, 75,
            esfuerzo=5,
        ),
        ejercicio_por_distancia(
            "Caminata del granjero con mancuernas", 2, 3, 30, 60,
            esfuerzo=5,
        ),
        ejercicio_por_distancia(
            "Remo en máquina ergométrica", 3, 2, 300, 60,
            esfuerzo=5,
        ),
        ejercicio_por_repeticiones(
            "Press Pallof en polea", 4, 3, 10, 12, 45,
            esfuerzo=5,
        ),
        ejercicio_por_repeticiones(
            "Bird dog", 5, 3, 8, 10, 45, esfuerzo=5,
        ),
        ejercicio_por_tiempo(
            "Plancha frontal sobre antebrazos", 6, 2, 25, 45,
            obligatorio=False, esfuerzo=5,
        ),
    ],
})


DIAS_ESTETICA = [
    {
        "numero": 1,
        "nombre": "Piernas y glúteos",
        "enfoque": "Glúteos, cuádriceps, femorales y pantorrillas",
        "descripcion": "Trabajo de tren inferior con énfasis unilateral.",
        "activo": True,
    },
    {
        "numero": 2,
        "nombre": "Torso equilibrado",
        "enfoque": "Pecho, espalda, hombros y tríceps",
        "descripcion": "Empujes y tracciones para una postura equilibrada.",
        "activo": True,
    },
    {
        "numero": 3,
        "nombre": "Cadena posterior y core",
        "enfoque": "Femorales, espalda, bíceps y abdomen",
        "descripcion": "Fuerza posterior, estabilidad y acondicionamiento.",
        "activo": True,
    },
]

FASES_PERDER_PESO = [
    {
        "orden": 1,
        "nombre": "Adaptación y técnica",
        "semana_inicio": 1,
        "semana_fin": 4,
        "descripcion": (
            "Aprendizaje de los movimientos y creación de una base "
            "cardiovascular con intensidad moderada."
        ),
        "activo": True,
    },
    {
        "orden": 2,
        "nombre": "Aumento de capacidad",
        "semana_inicio": 5,
        "semana_fin": 8,
        "descripcion": (
            "Incremento gradual del trabajo de fuerza y del tiempo de "
            "acondicionamiento sin sacrificar la técnica."
        ),
        "activo": True,
    },
    {
        "orden": 3,
        "nombre": "Consolidación metabólica",
        "semana_inicio": 9,
        "semana_fin": 12,
        "descripcion": (
            "Consolidación de la resistencia, la fuerza y los hábitos de "
            "entrenamiento mediante una progresión controlada."
        ),
        "activo": True,
    },
]


DIAS_SALUD = [
    {
        "numero": 1,
        "nombre": "Piernas y movilidad",
        "enfoque": "Piernas, glúteos y equilibrio",
        "descripcion": "Patrones básicos de tren inferior y bajo impacto.",
        "activo": True,
    },
    {
        "numero": 2,
        "nombre": "Postura y tren superior",
        "enfoque": "Pecho, espalda, hombros y brazos",
        "descripcion": "Trabajo guiado para fuerza y postura cotidiana.",
        "activo": True,
    },
    {
        "numero": 3,
        "nombre": "Estabilidad de cuerpo completo",
        "enfoque": "Core, glúteos, equilibrio y capacidad funcional",
        "descripcion": "Control del tronco y movimientos funcionales.",
        "activo": True,
    },
]


DIAS_PERDER_PESO = [
    {
        "numero": 1,
        "nombre": "Piernas y cardio de bajo impacto",
        "enfoque": "Piernas, glúteos y capacidad cardiovascular",
        "descripcion": (
            "Fuerza de tren inferior seguida de acondicionamiento "
            "progresivo y controlado."
        ),
        "activo": True,
    },
    {
        "numero": 2,
        "nombre": "Tren superior completo",
        "enfoque": "Pecho, espalda, hombros y brazos",
        "descripcion": (
            "Empujes y tracciones equilibrados para conservar fuerza y "
            "masa muscular durante el proceso."
        ),
        "activo": True,
    },
    {
        "numero": 3,
        "nombre": "Cuerpo completo y acondicionamiento",
        "enfoque": "Cadena posterior, core y resistencia",
        "descripcion": (
            "Sesión funcional para mejorar la estabilidad, el gasto "
            "energético y la capacidad de trabajo."
        ),
        "activo": True,
    },
]

PLANES_INICIALES = [
    {
        "nombre": "Estética inicial de 12 semanas",
        "objetivo": ObjetivoChoice.ESTETICO,
        "dias": DIAS_ESTETICA,
        "programacion": PROGRAMACION_ESTETICA,
        "descripcion": (
            "Programa inicial de fuerza y acondicionamiento para mejorar "
            "la composición corporal con una progresión segura."
        ),
    },
    {
        "nombre": "Hipertrofia inicial de 12 semanas",
        "objetivo": ObjetivoChoice.HIPERTROFIA,
        "descripcion": (
            "Plan progresivo para aprender los ejercicios principales, "
            "aumentar el volumen y desarrollar masa muscular."
        ),
    },
    {
        "nombre": "Salud y movimiento de 12 semanas",
        "objetivo": ObjetivoChoice.SALUD,
        "dias": DIAS_SALUD,
        "programacion": PROGRAMACION_SALUD,
        "descripcion": (
            "Programa de cuerpo completo orientado a mejorar fuerza, "
            "movilidad y capacidad física general."
        ),
    },
    {
        "nombre": "Pérdida de peso inicial de 12 semanas",
        "objetivo": ObjetivoChoice.PERDER_PESO,
        "fases": FASES_PERDER_PESO,
        "dias": DIAS_PERDER_PESO,
        "programacion": PROGRAMACION_PERDER_PESO,
        "descripcion": (
            "Programa progresivo de fuerza y acondicionamiento para aumentar "
            "el gasto energético, conservar masa muscular y construir una "
            "rutina sostenible."
        ),
    },
]


class Command(BaseCommand):
    help = "Carga los planes iniciales de MaikerGym para cada objetivo."

    @transaction.atomic
    def handle(self, *args, **options):
        PlanEntrenamiento.objects.filter(
            nombre__in=[
                "Nutrición y acondicionamiento de 12 semanas",
                "Recuperación progresiva de 12 semanas",
            ],
        ).update(activo=False)

        for configuracion in PLANES_INICIALES:
            self.cargar_plan(configuracion)

    def cargar_plan(self, configuracion):
        plan, plan_creado = PlanEntrenamiento.objects.update_or_create(
            nombre=configuracion["nombre"],
            defaults={
                "objetivo": configuracion["objetivo"],
                "nivel": NivelEjercicioChoice.PRINCIPIANTE,
                "descripcion": configuracion["descripcion"],
                "duracion_semanas": 12,
                "dias_por_semana": 3,
                "activo": True,
            },
        )

        contadores = {
            "fases_creadas": 0,
            "fases_actualizadas": 0,
            "dias_creados": 0,
            "dias_actualizados": 0,
            "programados_creados": 0,
            "programados_actualizados": 0,
            "programados_desactivados": 0,
        }

        dias_configurados = configuracion.get("dias", DIAS)
        fases_configuradas = configuracion.get("fases", FASES)
        programacion = configuracion.get("programacion", PROGRAMACION)

        for datos in fases_configuradas:
            valores = datos.copy()
            orden = valores.pop("orden")
            fase, fase_creada = FasePlan.objects.update_or_create(
                plan=plan,
                orden=orden,
                defaults=valores,
            )
            clave_fase = (
                "fases_creadas"
                if fase_creada
                else "fases_actualizadas"
            )
            contadores[clave_fase] += 1

            for datos_dia in dias_configurados:
                valores_dia = datos_dia.copy()
                numero_dia = valores_dia.pop("numero")
                dia, dia_creado = DiaPlan.objects.update_or_create(
                    fase=fase,
                    numero=numero_dia,
                    defaults=valores_dia,
                )
                clave_dia = (
                    "dias_creados"
                    if dia_creado
                    else "dias_actualizados"
                )
                contadores[clave_dia] += 1

                ejercicios_del_dia = programacion.get(
                    fase.orden,
                    {},
                ).get(numero_dia, [])
                self.sincronizar_ejercicios_del_dia(
                    dia,
                    ejercicios_del_dia,
                    contadores,
                )

        estado_plan = "creado" if plan_creado else "actualizado"
        self.stdout.write(
            self.style.SUCCESS(
                f"Plan {estado_plan}: {plan.nombre}. "
                f"Fases creadas: {contadores['fases_creadas']}. "
                f"Fases actualizadas: {contadores['fases_actualizadas']}. "
                f"Días creados: {contadores['dias_creados']}. "
                f"Días actualizados: {contadores['dias_actualizados']}. "
                "Ejercicios creados: "
                f"{contadores['programados_creados']}. "
                "Ejercicios actualizados: "
                f"{contadores['programados_actualizados']}. "
                "Ejercicios anteriores desactivados: "
                f"{contadores['programados_desactivados']}."
            )
        )

    def sincronizar_ejercicios_del_dia(
        self,
        dia,
        ejercicios_del_dia,
        contadores,
    ):
        nombres = [
            datos["ejercicio"]
            for datos in ejercicios_del_dia
        ]
        ejercicios = {
            ejercicio.nombre: ejercicio
            for ejercicio in Ejercicio.objects.filter(nombre__in=nombres)
        }
        faltantes = sorted(set(nombres) - set(ejercicios))
        if faltantes:
            raise CommandError(
                "No existen los ejercicios: "
                f"{', '.join(faltantes)}. "
                "Ejecuta primero cargar_ejercicios."
            )

        ordenes_deseados = {
            datos["orden"]
            for datos in ejercicios_del_dia
        }

        for datos_programados in ejercicios_del_dia:
            valores_programados = datos_programados.copy()
            nombre_ejercicio = valores_programados.pop("ejercicio")
            ejercicio = ejercicios[nombre_ejercicio]
            orden_deseado = valores_programados["orden"]

            ocupante = (
                EjercicioProgramado.objects
                .select_for_update()
                .filter(dia=dia, orden=orden_deseado)
                .exclude(ejercicio=ejercicio)
                .first()
            )
            if ocupante is not None:
                ordenes_usados = set(
                    EjercicioProgramado.objects.filter(dia=dia)
                    .values_list("orden", flat=True)
                )
                orden_temporal = next(
                    (
                        orden
                        for orden in range(50, 0, -1)
                        if orden not in ordenes_usados
                        and orden not in ordenes_deseados
                    ),
                    None,
                )
                if orden_temporal is None:
                    raise CommandError(
                        f"No hay un orden temporal libre en {dia}."
                    )
                ocupante.orden = orden_temporal
                ocupante.activo = False
                ocupante.save(update_fields=["orden", "activo"])

            _, programado_creado = (
                EjercicioProgramado.objects.update_or_create(
                    dia=dia,
                    ejercicio=ejercicio,
                    defaults=valores_programados,
                )
            )
            clave_programado = (
                "programados_creados"
                if programado_creado
                else "programados_actualizados"
            )
            contadores[clave_programado] += 1

        desactivados = (
            EjercicioProgramado.objects
            .filter(dia=dia, activo=True)
            .exclude(ejercicio__nombre__in=nombres)
            .update(activo=False)
        )
        contadores["programados_desactivados"] += desactivados
