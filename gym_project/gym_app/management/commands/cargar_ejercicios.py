from django.core.management.base import BaseCommand
from django.db import transaction

from gym_project.gym_app.models import (
    Ejercicio,
    GrupoMuscularChoice,
    NivelEjercicioChoice,
    TipoEquipoChoice,
    TipoMedicionChoice,
)


EJERCICIOS = [
    {
        "nombre": "Sentadilla con barra",
        "descripcion": (
            "Ejercicio compuesto para fortalecer principalmente "
            "cuádriceps, glúteos y femorales."
        ),
        "instrucciones": "\n".join([
            "Ajusta la barra sobre el rack a una altura segura.",
            "Coloca la barra sobre la parte superior de la espalda.",
            "Separa los pies aproximadamente al ancho de los hombros.",
            "Mantén el pecho elevado y la espalda neutral.",
            "Desciende llevando la cadera hacia atrás.",
            "Empuja el suelo para regresar a la posición inicial.",
        ]),
        "errores_comunes": "\n".join([
            "Juntar las rodillas durante el movimiento.",
            "Levantar los talones.",
            "Inclinar excesivamente la espalda.",
            "Utilizar una carga que no pueda controlarse.",
        ]),
        "precauciones": (
            "Utiliza seguros en la barra y solicita supervisión "
            "cuando trabajes con cargas elevadas."
        ),
        "grupo_muscular": GrupoMuscularChoice.CUADRICEPS,
        "musculos_secundarios": "Glúteos, femorales y abdomen",
        "nivel": NivelEjercicioChoice.INTERMEDIO,
        "tipo_equipo": TipoEquipoChoice.BARRA,
        "equipo_necesario": (
            "Barra olímpica, discos y rack para sentadillas"
        ),
        "tipo_medicion": TipoMedicionChoice.REPETICIONES,
        "puntos_base": 15,
        "activo": True,
    },
    {
        "nombre": "Press de banca con barra",
        "descripcion": (
            "Ejercicio compuesto de empuje para desarrollar el pecho, "
            "los tríceps y la parte anterior de los hombros."
        ),
        "instrucciones": "\n".join([
            "Acuéstate sobre el banco con los pies apoyados en el suelo.",
            "Sujeta la barra un poco más ancho que los hombros.",
            "Retira la barra del soporte con los brazos extendidos.",
            "Desciende la barra de forma controlada hacia el pecho.",
            "Empuja la barra hasta extender los brazos sin bloquearlos.",
        ]),
        "errores_comunes": "\n".join([
            "Rebotar la barra contra el pecho.",
            "Levantar los pies del suelo.",
            "Separar excesivamente los codos.",
            "Perder el control durante el descenso.",
        ]),
        "precauciones": (
            "Usa seguros y solicita la ayuda de un compañero "
            "cuando entrenes con una carga alta."
        ),
        "grupo_muscular": GrupoMuscularChoice.PECHO,
        "musculos_secundarios": "Tríceps y hombros",
        "nivel": NivelEjercicioChoice.INTERMEDIO,
        "tipo_equipo": TipoEquipoChoice.BARRA,
        "equipo_necesario": (
            "Banco plano, barra olímpica, discos y soporte"
        ),
        "tipo_medicion": TipoMedicionChoice.REPETICIONES,
        "puntos_base": 15,
        "activo": True,
    },
    {
        "nombre": "Jalón al pecho en polea",
        "descripcion": (
            "Ejercicio de tracción vertical para fortalecer la espalda, "
            "especialmente el dorsal ancho."
        ),
        "instrucciones": "\n".join([
            "Ajusta el asiento y fija las piernas bajo las almohadillas.",
            "Sujeta la barra con un agarre ligeramente amplio.",
            "Mantén el pecho elevado y el abdomen firme.",
            "Lleva la barra hacia la parte superior del pecho.",
            "Regresa lentamente hasta extender los brazos.",
        ]),
        "errores_comunes": "\n".join([
            "Llevar la barra detrás de la cabeza.",
            "Balancear excesivamente el cuerpo.",
            "Encoger los hombros.",
            "Soltar el peso sin controlar el regreso.",
        ]),
        "precauciones": (
            "No lleves la barra detrás de la nuca y selecciona "
            "una carga que permita controlar todo el recorrido."
        ),
        "grupo_muscular": GrupoMuscularChoice.ESPALDA,
        "musculos_secundarios": "Bíceps y antebrazos",
        "nivel": NivelEjercicioChoice.PRINCIPIANTE,
        "tipo_equipo": TipoEquipoChoice.POLEA,
        "equipo_necesario": "Máquina de polea alta y barra para jalón",
        "tipo_medicion": TipoMedicionChoice.REPETICIONES,
        "puntos_base": 10,
        "activo": True,
    },
]

EJERCICIOS.extend([
    {
        "nombre": "Prensa de piernas en máquina",
        "descripcion": (
            "Ejercicio guiado para fortalecer los cuádriceps y glúteos "
            "utilizando una máquina de prensa inclinada."
        ),
        "instrucciones": "\n".join([
            "Ajusta el asiento para mantener la espalda apoyada.",
            "Coloca los pies al ancho de los hombros sobre la plataforma.",
            "Libera los seguros de la máquina.",
            "Flexiona las rodillas de forma controlada.",
            "Empuja la plataforma sin bloquear completamente las rodillas.",
            "Activa nuevamente los seguros al finalizar.",
        ]),
        "errores_comunes": "\n".join([
            "Despegar la espalda baja del asiento.",
            "Juntar las rodillas.",
            "Bloquear completamente las piernas.",
            "Descender más de lo que permite la movilidad.",
        ]),
        "precauciones": (
            "Comprueba los seguros antes de comenzar y utiliza una carga "
            "que permita mantener la espalda apoyada."
        ),
        "grupo_muscular": GrupoMuscularChoice.CUADRICEPS,
        "musculos_secundarios": "Glúteos, femorales y pantorrillas",
        "nivel": NivelEjercicioChoice.PRINCIPIANTE,
        "tipo_equipo": TipoEquipoChoice.MAQUINA,
        "equipo_necesario": "Máquina de prensa de piernas y discos",
        "tipo_medicion": TipoMedicionChoice.REPETICIONES,
        "puntos_base": 10,
        "activo": True,
    },
    {
        "nombre": "Peso muerto rumano con barra",
        "descripcion": (
            "Movimiento de bisagra de cadera para fortalecer femorales, "
            "glúteos y la musculatura estabilizadora de la espalda."
        ),
        "instrucciones": "\n".join([
            "Sujeta la barra frente a los muslos.",
            "Separa los pies aproximadamente al ancho de la cadera.",
            "Flexiona ligeramente las rodillas.",
            "Lleva la cadera hacia atrás manteniendo la espalda neutral.",
            "Desciende la barra cerca de las piernas.",
            "Contrae los glúteos para regresar a la posición inicial.",
        ]),
        "errores_comunes": "\n".join([
            "Redondear la espalda.",
            "Separar la barra del cuerpo.",
            "Convertir el movimiento en una sentadilla.",
            "Descender más allá de la movilidad disponible.",
        ]),
        "precauciones": (
            "La barra debe permanecer cerca del cuerpo. Detén el descenso "
            "si no puedes conservar la espalda en posición neutral."
        ),
        "grupo_muscular": GrupoMuscularChoice.FEMORALES,
        "musculos_secundarios": "Glúteos, espalda baja y antebrazos",
        "nivel": NivelEjercicioChoice.INTERMEDIO,
        "tipo_equipo": TipoEquipoChoice.BARRA,
        "equipo_necesario": "Barra olímpica y discos de peso",
        "tipo_medicion": TipoMedicionChoice.REPETICIONES,
        "puntos_base": 15,
        "activo": True,
    },
    {
        "nombre": "Hip thrust con barra",
        "descripcion": (
            "Ejercicio de extensión de cadera enfocado principalmente "
            "en el desarrollo y fortalecimiento de los glúteos."
        ),
        "instrucciones": "\n".join([
            "Apoya la parte superior de la espalda contra un banco.",
            "Coloca la barra protegida sobre la cadera.",
            "Apoya completamente los pies en el suelo.",
            "Eleva la cadera contrayendo los glúteos.",
            "Mantén el abdomen firme en la parte superior.",
            "Desciende la cadera de forma controlada.",
        ]),
        "errores_comunes": "\n".join([
            "Extender excesivamente la espalda baja.",
            "Impulsar la barra sin control.",
            "Colocar los pies demasiado lejos o demasiado cerca.",
            "Dejar caer la cadera durante el descenso.",
        ]),
        "precauciones": (
            "Utiliza una almohadilla protectora en la barra y asegúrate "
            "de que el banco no pueda desplazarse."
        ),
        "grupo_muscular": GrupoMuscularChoice.GLUTEOS,
        "musculos_secundarios": "Femorales y cuádriceps",
        "nivel": NivelEjercicioChoice.INTERMEDIO,
        "tipo_equipo": TipoEquipoChoice.BARRA,
        "equipo_necesario": (
            "Barra olímpica, discos, banco y almohadilla protectora"
        ),
        "tipo_medicion": TipoMedicionChoice.REPETICIONES,
        "puntos_base": 15,
        "activo": True,
    },
])

EJERCICIOS.extend([
    {
        "nombre": "Extensión de cuádriceps en máquina",
        "descripcion": (
            "Ejercicio de aislamiento para fortalecer los cuádriceps "
            "utilizando una máquina de extensión de piernas."
        ),
        "instrucciones": "\n".join([
            "Ajusta el respaldo y el rodillo a la altura de los tobillos.",
            "Mantén la espalda apoyada contra el asiento.",
            "Extiende las rodillas elevando el rodillo.",
            "Contrae los cuádriceps en la parte superior.",
            "Regresa lentamente a la posición inicial.",
        ]),
        "errores_comunes": "\n".join([
            "Utilizar impulso para elevar el peso.",
            "Levantar la cadera del asiento.",
            "Dejar caer el peso durante el descenso.",
            "Usar una carga que impida completar el recorrido.",
        ]),
        "precauciones": (
            "Alinea el eje de la máquina con las rodillas y evita "
            "movimientos bruscos."
        ),
        "grupo_muscular": GrupoMuscularChoice.CUADRICEPS,
        "musculos_secundarios": "",
        "nivel": NivelEjercicioChoice.PRINCIPIANTE,
        "tipo_equipo": TipoEquipoChoice.MAQUINA,
        "equipo_necesario": "Máquina de extensión de piernas",
        "tipo_medicion": TipoMedicionChoice.REPETICIONES,
        "puntos_base": 8,
        "activo": True,
    },
    {
        "nombre": "Curl femoral tumbado en máquina",
        "descripcion": (
            "Ejercicio de aislamiento para trabajar la musculatura "
            "posterior del muslo."
        ),
        "instrucciones": "\n".join([
            "Acuéstate boca abajo sobre la máquina.",
            "Coloca el rodillo sobre la parte posterior de los tobillos.",
            "Mantén la cadera apoyada contra el banco.",
            "Flexiona las rodillas llevando los talones hacia los glúteos.",
            "Desciende el peso lentamente.",
        ]),
        "errores_comunes": "\n".join([
            "Levantar la cadera.",
            "Arquear excesivamente la espalda.",
            "Mover el peso con impulso.",
            "Soltar el peso durante el descenso.",
        ]),
        "precauciones": (
            "Ajusta correctamente el rodillo y mantén la cadera "
            "apoyada durante todo el movimiento."
        ),
        "grupo_muscular": GrupoMuscularChoice.FEMORALES,
        "musculos_secundarios": "Pantorrillas",
        "nivel": NivelEjercicioChoice.PRINCIPIANTE,
        "tipo_equipo": TipoEquipoChoice.MAQUINA,
        "equipo_necesario": "Máquina de curl femoral tumbado",
        "tipo_medicion": TipoMedicionChoice.REPETICIONES,
        "puntos_base": 8,
        "activo": True,
    },
    {
        "nombre": "Abducción de cadera en máquina",
        "descripcion": (
            "Ejercicio para fortalecer la parte lateral de los glúteos "
            "mediante la separación controlada de las piernas."
        ),
        "instrucciones": "\n".join([
            "Ajusta el asiento y las almohadillas laterales.",
            "Apoya completamente la espalda.",
            "Mantén los pies sobre los soportes.",
            "Separa las piernas de forma controlada.",
            "Regresa lentamente sin dejar caer el peso.",
        ]),
        "errores_comunes": "\n".join([
            "Balancear el torso.",
            "Cerrar las piernas sin controlar el peso.",
            "Utilizar un recorrido demasiado corto.",
            "Separar las piernas mediante impulso.",
        ]),
        "precauciones": (
            "Selecciona una amplitud cómoda y evita forzar la articulación "
            "de la cadera."
        ),
        "grupo_muscular": GrupoMuscularChoice.GLUTEOS,
        "musculos_secundarios": "Abductores de la cadera",
        "nivel": NivelEjercicioChoice.PRINCIPIANTE,
        "tipo_equipo": TipoEquipoChoice.MAQUINA,
        "equipo_necesario": "Máquina de abducción de cadera",
        "tipo_medicion": TipoMedicionChoice.REPETICIONES,
        "puntos_base": 8,
        "activo": True,
    },
    {
        "nombre": "Elevación de talones de pie en máquina",
        "descripcion": (
            "Ejercicio de gimnasio para fortalecer las pantorrillas "
            "mediante la elevación controlada de los talones."
        ),
        "instrucciones": "\n".join([
            "Coloca los hombros debajo de las almohadillas.",
            "Apoya la parte delantera de los pies sobre la plataforma.",
            "Mantén las rodillas ligeramente flexionadas.",
            "Eleva los talones todo lo posible.",
            "Desciende lentamente hasta sentir el estiramiento.",
        ]),
        "errores_comunes": "\n".join([
            "Realizar rebotes.",
            "Utilizar un recorrido incompleto.",
            "Girar los tobillos hacia los lados.",
            "Flexionar demasiado las rodillas.",
        ]),
        "precauciones": (
            "Mantén los tobillos alineados y realiza cada repetición "
            "sin rebotes."
        ),
        "grupo_muscular": GrupoMuscularChoice.PANTORRILLAS,
        "musculos_secundarios": "",
        "nivel": NivelEjercicioChoice.PRINCIPIANTE,
        "tipo_equipo": TipoEquipoChoice.MAQUINA,
        "equipo_necesario": "Máquina de pantorrillas de pie",
        "tipo_medicion": TipoMedicionChoice.REPETICIONES,
        "puntos_base": 8,
        "activo": True,
    },
])

EJERCICIOS.extend([
    {
        "nombre": "Press inclinado con mancuernas",
        "descripcion": (
            "Ejercicio de empuje para desarrollar principalmente "
            "la parte superior del pecho."
        ),
        "instrucciones": "\n".join([
            "Ajusta el banco con una inclinación moderada.",
            "Apoya la espalda y los pies firmemente.",
            "Sostén las mancuernas a los lados del pecho.",
            "Empuja las mancuernas hacia arriba.",
            "Desciende de forma controlada.",
        ]),
        "errores_comunes": "\n".join([
            "Inclinar demasiado el banco.",
            "Chocar las mancuernas arriba.",
            "Separar excesivamente los codos.",
            "Arquear demasiado la espalda.",
        ]),
        "precauciones": (
            "Selecciona mancuernas que puedas colocar y retirar del banco "
            "sin perder el control."
        ),
        "grupo_muscular": GrupoMuscularChoice.PECHO,
        "musculos_secundarios": "Hombros y tríceps",
        "nivel": NivelEjercicioChoice.INTERMEDIO,
        "tipo_equipo": TipoEquipoChoice.MANCUERNAS,
        "equipo_necesario": "Banco inclinado y dos mancuernas",
        "tipo_medicion": TipoMedicionChoice.REPETICIONES,
        "puntos_base": 12,
        "activo": True,
    },
    {
        "nombre": "Aperturas de pecho en máquina",
        "descripcion": (
            "Ejercicio de aislamiento para trabajar el pecho mediante "
            "un movimiento controlado de apertura y cierre."
        ),
        "instrucciones": "\n".join([
            "Ajusta el asiento para alinear los brazos con el pecho.",
            "Apoya completamente la espalda.",
            "Sujeta las empuñaduras.",
            "Junta los brazos frente al pecho.",
            "Regresa lentamente hasta una apertura cómoda.",
        ]),
        "errores_comunes": "\n".join([
            "Separar la espalda del asiento.",
            "Cerrar los brazos mediante impulso.",
            "Abrir más allá de la movilidad disponible.",
            "Dejar regresar el peso sin control.",
        ]),
        "precauciones": (
            "No fuerces la apertura de los hombros y mantén la espalda "
            "apoyada durante todo el ejercicio."
        ),
        "grupo_muscular": GrupoMuscularChoice.PECHO,
        "musculos_secundarios": "Hombros",
        "nivel": NivelEjercicioChoice.PRINCIPIANTE,
        "tipo_equipo": TipoEquipoChoice.MAQUINA,
        "equipo_necesario": "Máquina de aperturas o pec deck",
        "tipo_medicion": TipoMedicionChoice.REPETICIONES,
        "puntos_base": 8,
        "activo": True,
    },
    {
        "nombre": "Press militar sentado con mancuernas",
        "descripcion": (
            "Ejercicio de empuje vertical para fortalecer los hombros "
            "y los tríceps."
        ),
        "instrucciones": "\n".join([
            "Ajusta el respaldo del banco en posición vertical.",
            "Apoya la espalda y los pies firmemente.",
            "Coloca las mancuernas a la altura de los hombros.",
            "Empuja las mancuernas hacia arriba.",
            "Desciende lentamente hasta la posición inicial.",
        ]),
        "errores_comunes": "\n".join([
            "Arquear excesivamente la espalda.",
            "Chocar las mancuernas arriba.",
            "Bajar los codos demasiado.",
            "Realizar el movimiento mediante impulso.",
        ]),
        "precauciones": (
            "Mantén el abdomen firme y evita utilizar una carga que "
            "obligue a arquear la espalda."
        ),
        "grupo_muscular": GrupoMuscularChoice.HOMBROS,
        "musculos_secundarios": "Tríceps",
        "nivel": NivelEjercicioChoice.INTERMEDIO,
        "tipo_equipo": TipoEquipoChoice.MANCUERNAS,
        "equipo_necesario": "Banco con respaldo y dos mancuernas",
        "tipo_medicion": TipoMedicionChoice.REPETICIONES,
        "puntos_base": 12,
        "activo": True,
    },
    {
        "nombre": "Elevaciones laterales con mancuernas",
        "descripcion": (
            "Ejercicio de aislamiento para desarrollar la zona lateral "
            "de los hombros."
        ),
        "instrucciones": "\n".join([
            "Sostén una mancuerna en cada mano.",
            "Mantén los codos ligeramente flexionados.",
            "Eleva los brazos hacia los lados.",
            "Detente aproximadamente a la altura de los hombros.",
            "Desciende las mancuernas lentamente.",
        ]),
        "errores_comunes": "\n".join([
            "Balancear el cuerpo.",
            "Elevar los hombros hacia las orejas.",
            "Subir las manos demasiado.",
            "Dejar caer las mancuernas.",
        ]),
        "precauciones": (
            "Utiliza una carga ligera que permita realizar el movimiento "
            "sin balancear el torso."
        ),
        "grupo_muscular": GrupoMuscularChoice.HOMBROS,
        "musculos_secundarios": "Trapecios",
        "nivel": NivelEjercicioChoice.PRINCIPIANTE,
        "tipo_equipo": TipoEquipoChoice.MANCUERNAS,
        "equipo_necesario": "Dos mancuernas",
        "tipo_medicion": TipoMedicionChoice.REPETICIONES,
        "puntos_base": 8,
        "activo": True,
    },
    {
        "nombre": "Extensión de tríceps en polea",
        "descripcion": (
            "Ejercicio de aislamiento para fortalecer los tríceps "
            "utilizando una polea alta."
        ),
        "instrucciones": "\n".join([
            "Coloca una barra o cuerda en la polea alta.",
            "Mantén los codos junto al cuerpo.",
            "Extiende los brazos hacia abajo.",
            "Contrae los tríceps al final del movimiento.",
            "Regresa lentamente sin mover los codos.",
        ]),
        "errores_comunes": "\n".join([
            "Separar los codos.",
            "Inclinar excesivamente el torso.",
            "Mover los hombros durante cada repetición.",
            "Dejar subir el peso sin control.",
        ]),
        "precauciones": (
            "Mantén las muñecas alineadas y selecciona una carga que "
            "permita conservar los codos inmóviles."
        ),
        "grupo_muscular": GrupoMuscularChoice.TRICEPS,
        "musculos_secundarios": "Antebrazos",
        "nivel": NivelEjercicioChoice.PRINCIPIANTE,
        "tipo_equipo": TipoEquipoChoice.POLEA,
        "equipo_necesario": "Polea alta y accesorio de barra o cuerda",
        "tipo_medicion": TipoMedicionChoice.REPETICIONES,
        "puntos_base": 8,
        "activo": True,
    },
])
EJERCICIOS.extend([
    {
        "nombre": "Remo sentado en polea",
        "descripcion": (
            "Ejercicio de tracción horizontal para fortalecer la espalda "
            "utilizando una polea baja."
        ),
        "instrucciones": "\n".join([
            "Siéntate con los pies apoyados en la plataforma.",
            "Sujeta el accesorio con los brazos extendidos.",
            "Mantén la espalda neutral y el pecho elevado.",
            "Lleva el accesorio hacia el abdomen.",
            "Regresa lentamente hasta extender los brazos.",
        ]),
        "errores_comunes": "\n".join([
            "Balancear el torso.",
            "Redondear la espalda.",
            "Elevar los hombros.",
            "Soltar el peso sin control.",
        ]),
        "precauciones": (
            "Mantén la espalda neutral y evita impulsarte hacia atrás "
            "para mover una carga excesiva."
        ),
        "grupo_muscular": GrupoMuscularChoice.ESPALDA,
        "musculos_secundarios": "Bíceps, antebrazos y hombros",
        "nivel": NivelEjercicioChoice.PRINCIPIANTE,
        "tipo_equipo": TipoEquipoChoice.POLEA,
        "equipo_necesario": "Polea baja y accesorio de remo",
        "tipo_medicion": TipoMedicionChoice.REPETICIONES,
        "puntos_base": 10,
        "activo": True,
    },
    {
        "nombre": "Remo inclinado con barra",
        "descripcion": (
            "Ejercicio compuesto con barra para desarrollar la espalda "
            "y mejorar la fuerza de tracción."
        ),
        "instrucciones": "\n".join([
            "Sujeta la barra con las manos al ancho de los hombros.",
            "Flexiona ligeramente las rodillas.",
            "Inclina el torso manteniendo la espalda neutral.",
            "Lleva la barra hacia la parte inferior del abdomen.",
            "Desciende la barra de manera controlada.",
        ]),
        "errores_comunes": "\n".join([
            "Redondear la espalda.",
            "Levantarse durante cada repetición.",
            "Separar demasiado la barra del cuerpo.",
            "Utilizar impulso con la cadera.",
        ]),
        "precauciones": (
            "Conserva la espalda neutral y utiliza una carga que permita "
            "mantener estable la posición del torso."
        ),
        "grupo_muscular": GrupoMuscularChoice.ESPALDA,
        "musculos_secundarios": "Bíceps, hombros y espalda baja",
        "nivel": NivelEjercicioChoice.INTERMEDIO,
        "tipo_equipo": TipoEquipoChoice.BARRA,
        "equipo_necesario": "Barra olímpica y discos",
        "tipo_medicion": TipoMedicionChoice.REPETICIONES,
        "puntos_base": 15,
        "activo": True,
    },
    {
        "nombre": "Dominadas asistidas en máquina",
        "descripcion": (
            "Ejercicio de tracción vertical realizado con asistencia "
            "para fortalecer espalda y brazos."
        ),
        "instrucciones": "\n".join([
            "Selecciona el nivel de asistencia.",
            "Sube con cuidado a la plataforma de la máquina.",
            "Sujeta las empuñaduras firmemente.",
            "Eleva el cuerpo acercando el pecho a las manos.",
            "Desciende lentamente hasta extender los brazos.",
        ]),
        "errores_comunes": "\n".join([
            "Balancear el cuerpo.",
            "Encoger los hombros.",
            "Realizar un recorrido incompleto.",
            "Dejarse caer durante el descenso.",
        ]),
        "precauciones": (
            "Sube y baja de la máquina con cuidado. Recuerda que aumentar "
            "la asistencia hace el ejercicio más sencillo."
        ),
        "grupo_muscular": GrupoMuscularChoice.ESPALDA,
        "musculos_secundarios": "Bíceps, antebrazos y abdomen",
        "nivel": NivelEjercicioChoice.PRINCIPIANTE,
        "tipo_equipo": TipoEquipoChoice.MAQUINA,
        "equipo_necesario": "Máquina de dominadas asistidas",
        "tipo_medicion": TipoMedicionChoice.REPETICIONES,
        "puntos_base": 12,
        "activo": True,
    },
    {
        "nombre": "Curl de bíceps con barra Z",
        "descripcion": (
            "Ejercicio de aislamiento para fortalecer los bíceps "
            "utilizando una barra con agarre angular."
        ),
        "instrucciones": "\n".join([
            "Sujeta la barra Z con las palmas hacia arriba.",
            "Mantén los codos cerca del torso.",
            "Flexiona los brazos llevando la barra hacia el pecho.",
            "Contrae los bíceps en la parte superior.",
            "Desciende la barra lentamente.",
        ]),
        "errores_comunes": "\n".join([
            "Balancear el torso.",
            "Mover los codos hacia adelante.",
            "Flexionar las muñecas.",
            "Dejar caer la barra durante el descenso.",
        ]),
        "precauciones": (
            "Mantén las muñecas alineadas y utiliza una carga que no "
            "requiera balancear el cuerpo."
        ),
        "grupo_muscular": GrupoMuscularChoice.BICEPS,
        "musculos_secundarios": "Antebrazos",
        "nivel": NivelEjercicioChoice.PRINCIPIANTE,
        "tipo_equipo": TipoEquipoChoice.BARRA,
        "equipo_necesario": "Barra Z y discos",
        "tipo_medicion": TipoMedicionChoice.REPETICIONES,
        "puntos_base": 8,
        "activo": True,
    },
    {
        "nombre": "Curl martillo con mancuernas",
        "descripcion": (
            "Ejercicio para fortalecer bíceps, braquial y antebrazos "
            "utilizando un agarre neutral."
        ),
        "instrucciones": "\n".join([
            "Sostén una mancuerna en cada mano.",
            "Orienta las palmas hacia el cuerpo.",
            "Mantén los codos junto al torso.",
            "Flexiona los brazos sin girar las muñecas.",
            "Desciende las mancuernas lentamente.",
        ]),
        "errores_comunes": "\n".join([
            "Balancear el torso.",
            "Separar los codos.",
            "Subir los hombros.",
            "Realizar el descenso sin control.",
        ]),
        "precauciones": (
            "Conserva las muñecas en posición neutral y evita utilizar "
            "impulso para levantar las mancuernas."
        ),
        "grupo_muscular": GrupoMuscularChoice.BICEPS,
        "musculos_secundarios": "Antebrazos",
        "nivel": NivelEjercicioChoice.PRINCIPIANTE,
        "tipo_equipo": TipoEquipoChoice.MANCUERNAS,
        "equipo_necesario": "Dos mancuernas",
        "tipo_medicion": TipoMedicionChoice.REPETICIONES,
        "puntos_base": 8,
        "activo": True,
    },
])
EJERCICIOS.extend([
    {
        "nombre": "Plancha frontal sobre antebrazos",
        "descripcion": (
            "Ejercicio isométrico para fortalecer el abdomen y mejorar "
            "la estabilidad del tronco."
        ),
        "instrucciones": "\n".join([
            "Apoya los antebrazos y las puntas de los pies.",
            "Coloca los codos debajo de los hombros.",
            "Mantén el cuerpo en línea recta.",
            "Contrae el abdomen y los glúteos.",
            "Conserva la posición durante el tiempo indicado.",
        ]),
        "errores_comunes": "\n".join([
            "Dejar caer la cadera.",
            "Elevar demasiado los glúteos.",
            "Contener la respiración.",
            "Adelantar excesivamente la cabeza.",
        ]),
        "precauciones": (
            "Detén el ejercicio si pierdes la posición del tronco. "
            "No debes sostener la postura mediante la espalda baja."
        ),
        "grupo_muscular": GrupoMuscularChoice.ABDOMEN,
        "musculos_secundarios": "Glúteos, hombros y espalda",
        "nivel": NivelEjercicioChoice.PRINCIPIANTE,
        "tipo_equipo": TipoEquipoChoice.PESO_CORPORAL,
        "equipo_necesario": "Colchoneta de ejercicio",
        "tipo_medicion": TipoMedicionChoice.TIEMPO,
        "puntos_base": 8,
        "activo": True,
    },
    {
        "nombre": "Crunch abdominal en máquina",
        "descripcion": (
            "Ejercicio guiado para fortalecer el abdomen mediante "
            "una flexión controlada del tronco."
        ),
        "instrucciones": "\n".join([
            "Ajusta el asiento y selecciona una carga adecuada.",
            "Apoya los pies y sujeta las empuñaduras.",
            "Contrae el abdomen para flexionar el tronco.",
            "Mantén brevemente la contracción.",
            "Regresa lentamente a la posición inicial.",
        ]),
        "errores_comunes": "\n".join([
            "Mover el peso mediante impulso.",
            "Tirar con los brazos.",
            "Utilizar una carga excesiva.",
            "Regresar sin controlar el peso.",
        ]),
        "precauciones": (
            "Realiza el recorrido de manera controlada y evita forzar "
            "el cuello durante la flexión."
        ),
        "grupo_muscular": GrupoMuscularChoice.ABDOMEN,
        "musculos_secundarios": "",
        "nivel": NivelEjercicioChoice.PRINCIPIANTE,
        "tipo_equipo": TipoEquipoChoice.MAQUINA,
        "equipo_necesario": "Máquina de crunch abdominal",
        "tipo_medicion": TipoMedicionChoice.REPETICIONES,
        "puntos_base": 8,
        "activo": True,
    },
    {
        "nombre": "Elevación de rodillas en silla romana",
        "descripcion": (
            "Ejercicio para fortalecer el abdomen elevando las rodillas "
            "con el cuerpo apoyado en una silla romana."
        ),
        "instrucciones": "\n".join([
            "Apoya los antebrazos y la espalda en la máquina.",
            "Mantén las piernas juntas.",
            "Eleva las rodillas hacia el pecho.",
            "Contrae el abdomen en la parte superior.",
            "Desciende las piernas lentamente.",
        ]),
        "errores_comunes": "\n".join([
            "Balancear las piernas.",
            "Arquear excesivamente la espalda.",
            "Realizar un recorrido demasiado corto.",
            "Dejar caer las piernas.",
        ]),
        "precauciones": (
            "Mantén la espalda apoyada y evita utilizar impulso "
            "para elevar las rodillas."
        ),
        "grupo_muscular": GrupoMuscularChoice.ABDOMEN,
        "musculos_secundarios": "Flexores de la cadera",
        "nivel": NivelEjercicioChoice.INTERMEDIO,
        "tipo_equipo": TipoEquipoChoice.MAQUINA,
        "equipo_necesario": "Silla romana con apoyo para antebrazos",
        "tipo_medicion": TipoMedicionChoice.REPETICIONES,
        "puntos_base": 10,
        "activo": True,
    },
    {
        "nombre": "Caminata del granjero con mancuernas",
        "descripcion": (
            "Ejercicio de desplazamiento con carga para trabajar agarre, "
            "piernas, abdomen y estabilidad corporal."
        ),
        "instrucciones": "\n".join([
            "Sujeta una mancuerna en cada mano.",
            "Mantén el pecho elevado y el abdomen firme.",
            "Camina con pasos cortos y controlados.",
            "Mantén las mancuernas junto al cuerpo.",
            "Completa la distancia indicada.",
        ]),
        "errores_comunes": "\n".join([
            "Inclinar el cuerpo hacia un lado.",
            "Encoger excesivamente los hombros.",
            "Caminar demasiado rápido.",
            "Perder la postura al girar.",
        ]),
        "precauciones": (
            "Utiliza una zona despejada y deja las mancuernas en el suelo "
            "mediante una flexión controlada de piernas."
        ),
        "grupo_muscular": GrupoMuscularChoice.CUERPO_COMPLETO,
        "musculos_secundarios": (
            "Antebrazos, trapecios, abdomen, glúteos y piernas"
        ),
        "nivel": NivelEjercicioChoice.INTERMEDIO,
        "tipo_equipo": TipoEquipoChoice.MANCUERNAS,
        "equipo_necesario": "Dos mancuernas y zona de desplazamiento",
        "tipo_medicion": TipoMedicionChoice.DISTANCIA,
        "puntos_base": 12,
        "activo": True,
    },
    {
        "nombre": "Caminata inclinada en caminadora",
        "descripcion": (
            "Ejercicio cardiovascular de bajo impacto realizado "
            "en una caminadora con inclinación."
        ),
        "instrucciones": "\n".join([
            "Sube a la caminadora antes de iniciar el movimiento.",
            "Selecciona una velocidad cómoda.",
            "Aumenta gradualmente la inclinación.",
            "Mantén una postura erguida durante la caminata.",
            "Reduce la velocidad antes de bajar.",
        ]),
        "errores_comunes": "\n".join([
            "Apoyar todo el peso sobre las barandas.",
            "Seleccionar demasiada velocidad.",
            "Inclinar excesivamente el torso.",
            "Bajar mientras la banda sigue moviéndose.",
        ]),
        "precauciones": (
            "Utiliza el sistema de parada de emergencia y aumenta "
            "la velocidad y la inclinación gradualmente."
        ),
        "grupo_muscular": GrupoMuscularChoice.CARDIO,
        "musculos_secundarios": "Glúteos, cuádriceps y pantorrillas",
        "nivel": NivelEjercicioChoice.PRINCIPIANTE,
        "tipo_equipo": TipoEquipoChoice.CARDIO,
        "equipo_necesario": "Caminadora con inclinación",
        "tipo_medicion": TipoMedicionChoice.TIEMPO,
        "puntos_base": 8,
        "activo": True,
    },
    {
        "nombre": "Remo en máquina ergométrica",
        "descripcion": (
            "Ejercicio cardiovascular de cuerpo completo realizado "
            "en una máquina de remo."
        ),
        "instrucciones": "\n".join([
            "Ajusta las correas de los pies.",
            "Sujeta el mango con los brazos extendidos.",
            "Empuja primero con las piernas.",
            "Inclina ligeramente el torso y lleva el mango al abdomen.",
            "Regresa extendiendo brazos, torso y finalmente piernas.",
        ]),
        "errores_comunes": "\n".join([
            "Tirar primero con los brazos.",
            "Redondear la espalda.",
            "Abrir los codos excesivamente.",
            "Regresar sin mantener el orden del movimiento.",
        ]),
        "precauciones": (
            "Mantén la espalda neutral y comienza con una resistencia "
            "moderada mientras aprendes la secuencia."
        ),
        "grupo_muscular": GrupoMuscularChoice.CUERPO_COMPLETO,
        "musculos_secundarios": "Espalda, piernas, brazos y abdomen",
        "nivel": NivelEjercicioChoice.INTERMEDIO,
        "tipo_equipo": TipoEquipoChoice.CARDIO,
        "equipo_necesario": "Máquina de remo ergométrica",
        "tipo_medicion": TipoMedicionChoice.DISTANCIA,
        "puntos_base": 12,
        "activo": True,
    },
    {
        "nombre": "Sentadilla goblet con mancuerna",
        "descripcion": (
            "Sentadilla con una mancuerna frente al pecho para reforzar "
            "la técnica, los cuádriceps y los glúteos."
        ),
        "instrucciones": "\n".join([
            "Sujeta una mancuerna vertical frente al pecho.",
            "Separa los pies aproximadamente al ancho de los hombros.",
            "Mantén el pecho elevado y el abdomen firme.",
            "Desciende llevando rodillas y puntas de los pies en la misma dirección.",
            "Empuja el suelo para volver a la posición inicial.",
        ]),
        "errores_comunes": "\n".join([
            "Separar la mancuerna del pecho.",
            "Juntar las rodillas durante el descenso.",
            "Levantar los talones.",
            "Redondear la espalda.",
        ]),
        "precauciones": (
            "Usa una carga que puedas sostener sin perder el apoyo completo "
            "de los pies ni la posición neutral de la espalda."
        ),
        "grupo_muscular": GrupoMuscularChoice.CUADRICEPS,
        "musculos_secundarios": "Glúteos, femorales y abdomen",
        "nivel": NivelEjercicioChoice.PRINCIPIANTE,
        "tipo_equipo": TipoEquipoChoice.MANCUERNAS,
        "equipo_necesario": "Una mancuerna",
        "tipo_medicion": TipoMedicionChoice.REPETICIONES,
        "puntos_base": 10,
        "activo": True,
    },
    {
        "nombre": "Zancada estática con mancuernas",
        "descripcion": (
            "Trabajo unilateral de piernas y glúteos manteniendo los pies "
            "en una posición estable durante toda la serie."
        ),
        "instrucciones": "\n".join([
            "Sostén una mancuerna a cada lado del cuerpo.",
            "Da un paso amplio y conserva ambos pies en esa posición.",
            "Baja la rodilla trasera hacia el suelo con el torso erguido.",
            "Mantén la rodilla delantera alineada con el pie.",
            "Empuja con el pie delantero y completa las repeticiones antes de cambiar.",
        ]),
        "errores_comunes": "\n".join([
            "Usar una base demasiado estrecha.",
            "Dejar caer la rodilla delantera hacia dentro.",
            "Impulsarse con la pierna trasera.",
            "Inclinar excesivamente el torso.",
        ]),
        "precauciones": (
            "Empieza sin carga si todavía no controlas el equilibrio y detén "
            "el descenso antes de sentir dolor en la rodilla."
        ),
        "grupo_muscular": GrupoMuscularChoice.GLUTEOS,
        "musculos_secundarios": "Cuádriceps, femorales y abdomen",
        "nivel": NivelEjercicioChoice.PRINCIPIANTE,
        "tipo_equipo": TipoEquipoChoice.MANCUERNAS,
        "equipo_necesario": "Par de mancuernas",
        "tipo_medicion": TipoMedicionChoice.REPETICIONES,
        "puntos_base": 12,
        "activo": True,
    },
    {
        "nombre": "Step-up al banco",
        "descripcion": (
            "Subida controlada a un banco bajo para desarrollar fuerza "
            "unilateral, equilibrio y estabilidad de cadera."
        ),
        "instrucciones": "\n".join([
            "Coloca todo el pie de trabajo sobre un banco estable.",
            "Inclina apenas el torso y mantén la rodilla alineada.",
            "Empuja el banco con la pierna elevada hasta quedar de pie.",
            "Evita impulsarte con el pie que permanece en el suelo.",
            "Desciende lentamente y completa las repeticiones antes de cambiar.",
        ]),
        "errores_comunes": "\n".join([
            "Apoyar solo la punta del pie sobre el banco.",
            "Usar un banco demasiado alto.",
            "Empujarse con la pierna inferior.",
            "Dejar caer la rodilla hacia dentro.",
        ]),
        "precauciones": (
            "Comprueba que el banco no se deslice y elige una altura que te "
            "permita subir sin perder la alineación de la rodilla."
        ),
        "grupo_muscular": GrupoMuscularChoice.GLUTEOS,
        "musculos_secundarios": "Cuádriceps, femorales y pantorrillas",
        "nivel": NivelEjercicioChoice.PRINCIPIANTE,
        "tipo_equipo": TipoEquipoChoice.PESO_CORPORAL,
        "equipo_necesario": "Banco o cajón bajo y estable",
        "tipo_medicion": TipoMedicionChoice.REPETICIONES,
        "puntos_base": 10,
        "activo": True,
    },
    {
        "nombre": "Puente de glúteos en suelo",
        "descripcion": (
            "Extensión de cadera desde el suelo para fortalecer glúteos "
            "con una carga articular moderada."
        ),
        "instrucciones": "\n".join([
            "Acuéstate boca arriba con las rodillas flexionadas.",
            "Apoya los pies completos al ancho de la cadera.",
            "Contrae el abdomen y empuja el suelo con los talones.",
            "Eleva la pelvis hasta alinear hombros, cadera y rodillas.",
            "Desciende de forma controlada sin arquear la espalda.",
        ]),
        "errores_comunes": "\n".join([
            "Empujar desde las puntas de los pies.",
            "Separar demasiado los pies del cuerpo.",
            "Hiperextender la zona lumbar.",
            "Dejar caer las rodillas hacia dentro.",
        ]),
        "precauciones": (
            "Detén la elevación cuando la cadera quede alineada; no busques "
            "altura adicional arqueando la zona lumbar."
        ),
        "grupo_muscular": GrupoMuscularChoice.GLUTEOS,
        "musculos_secundarios": "Femorales y abdomen",
        "nivel": NivelEjercicioChoice.PRINCIPIANTE,
        "tipo_equipo": TipoEquipoChoice.PESO_CORPORAL,
        "equipo_necesario": "Colchoneta",
        "tipo_medicion": TipoMedicionChoice.REPETICIONES,
        "puntos_base": 8,
        "activo": True,
    },
    {
        "nombre": "Press de pecho sentado en máquina",
        "descripcion": (
            "Empuje horizontal guiado para trabajar el pecho manteniendo "
            "la espalda estable contra el respaldo."
        ),
        "instrucciones": "\n".join([
            "Ajusta el asiento para que los agarres queden a la altura del pecho.",
            "Apoya cabeza, espalda y pies.",
            "Sujeta los mangos con las muñecas neutrales.",
            "Empuja hacia delante sin bloquear los codos.",
            "Regresa lentamente hasta un estiramiento cómodo.",
        ]),
        "errores_comunes": "\n".join([
            "Separar la espalda del respaldo.",
            "Encoger los hombros.",
            "Doblar las muñecas hacia atrás.",
            "Dejar que el peso regrese sin control.",
        ]),
        "precauciones": (
            "Ajusta el recorrido de la máquina para que los codos no queden "
            "excesivamente detrás del torso."
        ),
        "grupo_muscular": GrupoMuscularChoice.PECHO,
        "musculos_secundarios": "Tríceps y deltoides anterior",
        "nivel": NivelEjercicioChoice.PRINCIPIANTE,
        "tipo_equipo": TipoEquipoChoice.MAQUINA,
        "equipo_necesario": "Máquina de press de pecho",
        "tipo_medicion": TipoMedicionChoice.REPETICIONES,
        "puntos_base": 10,
        "activo": True,
    },
    {
        "nombre": "Face pull en polea",
        "descripcion": (
            "Tracción hacia el rostro para fortalecer la espalda alta, "
            "deltoides posterior y rotadores externos del hombro."
        ),
        "instrucciones": "\n".join([
            "Coloca una cuerda en una polea a la altura del rostro.",
            "Da un paso atrás y mantén el torso estable.",
            "Tira de la cuerda hacia la frente separando sus extremos.",
            "Lleva los codos hacia fuera sin elevar los hombros.",
            "Regresa despacio hasta extender casi por completo los brazos.",
        ]),
        "errores_comunes": "\n".join([
            "Convertir el gesto en un remo hacia el pecho.",
            "Arquear la zona lumbar.",
            "Encoger los hombros.",
            "Usar una carga que impida separar la cuerda.",
        ]),
        "precauciones": (
            "Usa una carga moderada y un recorrido sin dolor; no fuerces "
            "los hombros detrás de una posición cómoda."
        ),
        "grupo_muscular": GrupoMuscularChoice.ESPALDA,
        "musculos_secundarios": "Deltoides posterior y rotadores externos",
        "nivel": NivelEjercicioChoice.PRINCIPIANTE,
        "tipo_equipo": TipoEquipoChoice.POLEA,
        "equipo_necesario": "Polea ajustable y cuerda",
        "tipo_medicion": TipoMedicionChoice.REPETICIONES,
        "puntos_base": 10,
        "activo": True,
    },
    {
        "nombre": "Curl de bíceps en polea baja",
        "descripcion": (
            "Flexión de codos de pie con tensión continua proporcionada "
            "por una polea baja."
        ),
        "instrucciones": "\n".join([
            "Conecta una barra corta a la polea baja.",
            "Sujétala con las palmas hacia arriba y el torso erguido.",
            "Fija los codos junto a las costillas.",
            "Flexiona los codos sin mover los hombros.",
            "Extiende lentamente sin perder la tensión.",
        ]),
        "errores_comunes": "\n".join([
            "Balancear el torso.",
            "Adelantar los codos.",
            "Doblar las muñecas.",
            "Soltar la carga al descender.",
        ]),
        "precauciones": (
            "Mantén las muñecas alineadas y reduce la carga si necesitas "
            "usar impulso para completar la flexión."
        ),
        "grupo_muscular": GrupoMuscularChoice.BICEPS,
        "musculos_secundarios": "Braquial y antebrazos",
        "nivel": NivelEjercicioChoice.PRINCIPIANTE,
        "tipo_equipo": TipoEquipoChoice.POLEA,
        "equipo_necesario": "Polea baja y barra corta",
        "tipo_medicion": TipoMedicionChoice.REPETICIONES,
        "puntos_base": 8,
        "activo": True,
    },
    {
        "nombre": "Extensión de tríceps sobre la cabeza en polea",
        "descripcion": (
            "Extensión de codos con cuerda por encima de la cabeza para "
            "trabajar el tríceps en una posición alargada."
        ),
        "instrucciones": "\n".join([
            "Conecta una cuerda a la polea y colócate de espaldas a ella.",
            "Adopta una base estable con un pie ligeramente adelantado.",
            "Eleva los brazos y mantén los codos orientados al frente.",
            "Extiende los antebrazos sin mover los hombros.",
            "Regresa lentamente hasta una flexión cómoda.",
        ]),
        "errores_comunes": "\n".join([
            "Abrir demasiado los codos.",
            "Arquear la zona lumbar.",
            "Mover los hombros durante la extensión.",
            "Usar una carga excesiva.",
        ]),
        "precauciones": (
            "Evita este recorrido si causa dolor de hombro y mantén el "
            "abdomen activo para proteger la zona lumbar."
        ),
        "grupo_muscular": GrupoMuscularChoice.TRICEPS,
        "musculos_secundarios": "Hombros y abdomen",
        "nivel": NivelEjercicioChoice.INTERMEDIO,
        "tipo_equipo": TipoEquipoChoice.POLEA,
        "equipo_necesario": "Polea ajustable y cuerda",
        "tipo_medicion": TipoMedicionChoice.REPETICIONES,
        "puntos_base": 10,
        "activo": True,
    },
    {
        "nombre": "Press Pallof en polea",
        "descripcion": (
            "Ejercicio antirotación de pie para fortalecer el abdomen y "
            "la estabilidad del tronco frente a una fuerza lateral."
        ),
        "instrucciones": "\n".join([
            "Coloca la polea a la altura del pecho y ubícate de lado.",
            "Sujeta el mango con ambas manos frente al esternón.",
            "Separa los pies y activa abdomen y glúteos.",
            "Extiende los brazos sin permitir que el torso gire.",
            "Regresa el mango al pecho y cambia de lado al completar la serie.",
        ]),
        "errores_comunes": "\n".join([
            "Girar el torso hacia la polea.",
            "Juntar demasiado los pies.",
            "Elevar los hombros.",
            "Extender los brazos con impulso.",
        ]),
        "precauciones": (
            "Empieza con poca resistencia; la prioridad es impedir la "
            "rotación del tronco, no desplazar una carga alta."
        ),
        "grupo_muscular": GrupoMuscularChoice.ABDOMEN,
        "musculos_secundarios": "Glúteos y estabilizadores de hombro",
        "nivel": NivelEjercicioChoice.PRINCIPIANTE,
        "tipo_equipo": TipoEquipoChoice.POLEA,
        "equipo_necesario": "Polea ajustable y mango individual",
        "tipo_medicion": TipoMedicionChoice.REPETICIONES,
        "puntos_base": 10,
        "activo": True,
    },
    {
        "nombre": "Bird dog",
        "descripcion": (
            "Ejercicio de estabilidad en cuadrupedia que coordina brazo y "
            "pierna contrarios manteniendo la columna neutral."
        ),
        "instrucciones": "\n".join([
            "Coloca manos bajo hombros y rodillas bajo caderas.",
            "Activa el abdomen sin redondear la espalda.",
            "Extiende un brazo y la pierna contraria.",
            "Mantén la pelvis paralela al suelo.",
            "Regresa con control y alterna el lado.",
        ]),
        "errores_comunes": "\n".join([
            "Arquear la zona lumbar.",
            "Girar la pelvis.",
            "Elevar la pierna por encima de la cadera.",
            "Apresurar los cambios de lado.",
        ]),
        "precauciones": (
            "Reduce el alcance del brazo o la pierna si no puedes mantener "
            "el tronco estable y sin molestias."
        ),
        "grupo_muscular": GrupoMuscularChoice.ABDOMEN,
        "musculos_secundarios": "Glúteos, espalda y hombros",
        "nivel": NivelEjercicioChoice.PRINCIPIANTE,
        "tipo_equipo": TipoEquipoChoice.PESO_CORPORAL,
        "equipo_necesario": "Colchoneta",
        "tipo_medicion": TipoMedicionChoice.REPETICIONES,
        "puntos_base": 8,
        "activo": True,
    },
    {
        "nombre": "Aductores en máquina",
        "descripcion": "Ejercicio aislado para fortalecer los aductores de la cadera con recorrido controlado.",
        "instrucciones": "Ajusta el asiento y los apoyos. Mantén la espalda apoyada. Junta las piernas de forma controlada. Regresa sin golpear los topes.",
        "errores_comunes": "Usar impulso. Separar la espalda del respaldo. Cerrar las piernas de golpe.",
        "precauciones": "Empieza con carga ligera y reduce el recorrido si aparece molestia en la ingle o cadera.",
        "grupo_muscular": GrupoMuscularChoice.CUADRICEPS,
        "musculos_secundarios": "Aductores de la cadera y abdomen",
        "nivel": NivelEjercicioChoice.PRINCIPIANTE,
        "tipo_equipo": TipoEquipoChoice.MAQUINA,
        "equipo_necesario": "Máquina de aductores",
        "tipo_medicion": TipoMedicionChoice.REPETICIONES,
        "puntos_base": 8, "activo": True,
    },
    {
        "nombre": "Abductores en máquina",
        "descripcion": "Ejercicio aislado para fortalecer glúteo medio y músculos abductores de la cadera.",
        "instrucciones": "Ajusta el asiento y apoya la espalda. Abre las piernas sin mover el torso. Vuelve lentamente hasta la posición inicial.",
        "errores_comunes": "Arquear la espalda. Golpear los topes. Usar impulso con el torso.",
        "precauciones": "Mantén un rango cómodo de cadera y detente ante dolor articular.",
        "grupo_muscular": GrupoMuscularChoice.GLUTEOS,
        "musculos_secundarios": "Abductores de la cadera y abdomen",
        "nivel": NivelEjercicioChoice.PRINCIPIANTE,
        "tipo_equipo": TipoEquipoChoice.MAQUINA,
        "equipo_necesario": "Máquina de abductores",
        "tipo_medicion": TipoMedicionChoice.REPETICIONES,
        "puntos_base": 8, "activo": True,
    },
    {
        "nombre": "Curl de muñeca con mancuerna",
        "descripcion": "Fortalece los flexores del antebrazo mediante flexión controlada de la muñeca.",
        "instrucciones": "Apoya el antebrazo sobre un banco con la palma hacia arriba. Deja bajar la mancuerna con control. Flexiona la muñeca sin levantar el codo.",
        "errores_comunes": "Mover el codo. Usar una carga excesiva. Hacer rebotes.",
        "precauciones": "Usa poco peso y detente si aparece hormigueo o dolor en muñeca o codo.",
        "grupo_muscular": GrupoMuscularChoice.BICEPS,
        "musculos_secundarios": "Flexores del antebrazo",
        "nivel": NivelEjercicioChoice.PRINCIPIANTE,
        "tipo_equipo": TipoEquipoChoice.MANCUERNAS,
        "equipo_necesario": "Mancuerna y banco",
        "tipo_medicion": TipoMedicionChoice.REPETICIONES,
        "puntos_base": 6, "activo": True,
    },
    {
        "nombre": "Curl de muñeca inverso con mancuerna",
        "descripcion": "Fortalece los extensores del antebrazo mediante extensión controlada de la muñeca.",
        "instrucciones": "Apoya el antebrazo con la palma hacia abajo. Baja la mancuerna lentamente. Eleva el dorso de la mano sin separar el antebrazo del apoyo.",
        "errores_comunes": "Doblar el codo. Girar la muñeca. Usar impulso.",
        "precauciones": "Realiza el movimiento con carga ligera y sin dolor en la cara externa del codo.",
        "grupo_muscular": GrupoMuscularChoice.BICEPS,
        "musculos_secundarios": "Extensores del antebrazo",
        "nivel": NivelEjercicioChoice.PRINCIPIANTE,
        "tipo_equipo": TipoEquipoChoice.MANCUERNAS,
        "equipo_necesario": "Mancuerna y banco",
        "tipo_medicion": TipoMedicionChoice.REPETICIONES,
        "puntos_base": 6, "activo": True,
    },
    {
        "nombre": "Curl con agarre en pronación",
        "descripcion": "Curl de brazos con palmas hacia abajo para trabajar braquial y antebrazos.",
        "instrucciones": "Sujeta barra Z o barra recta con palmas hacia abajo. Mantén los codos junto al cuerpo. Flexiona sin mover los hombros y baja lentamente.",
        "errores_comunes": "Balancear el torso. Doblar las muñecas. Separar los codos.",
        "precauciones": "Elige una carga moderada y conserva las muñecas neutras durante toda la serie.",
        "grupo_muscular": GrupoMuscularChoice.BICEPS,
        "musculos_secundarios": "Braquial y extensores del antebrazo",
        "nivel": NivelEjercicioChoice.INTERMEDIO,
        "tipo_equipo": TipoEquipoChoice.BARRA,
        "equipo_necesario": "Barra Z o barra recta",
        "tipo_medicion": TipoMedicionChoice.REPETICIONES,
        "puntos_base": 8, "activo": True,
    },
    {
        "nombre": "Extensión de antebrazo en polea",
        "descripcion": "Ejercicio de extensión de muñeca en polea para los extensores del antebrazo.",
        "instrucciones": "Coloca la polea baja y apoya los antebrazos. Sujeta la barra con palmas hacia abajo. Extiende las muñecas de forma suave y vuelve con control.",
        "errores_comunes": "Mover los codos. Tirar con los hombros. Doblar las muñecas hacia los lados.",
        "precauciones": "Usa carga ligera; suspende el ejercicio si hay dolor, hormigueo o pérdida de fuerza.",
        "grupo_muscular": GrupoMuscularChoice.BICEPS,
        "musculos_secundarios": "Extensores del antebrazo",
        "nivel": NivelEjercicioChoice.INTERMEDIO,
        "tipo_equipo": TipoEquipoChoice.POLEA,
        "equipo_necesario": "Polea baja y barra recta corta",
        "tipo_medicion": TipoMedicionChoice.REPETICIONES,
        "puntos_base": 8, "activo": True,
    },
])
class Command(BaseCommand):
    help = "Carga o actualiza el catálogo inicial de ejercicios."

    @transaction.atomic
    def handle(self, *args, **options):
        creados = 0
        actualizados = 0

        for datos in EJERCICIOS:
            valores = datos.copy()
            nombre = valores.pop("nombre")

            ejercicio, fue_creado = Ejercicio.objects.update_or_create(
                nombre=nombre,
                defaults=valores,
            )

            if fue_creado:
                creados += 1
            else:
                actualizados += 1

            self.stdout.write(f"Procesado: {ejercicio.nombre}")

        self.stdout.write(
            self.style.SUCCESS(
                "Catálogo cargado correctamente. "
                f"Creados: {creados}. "
                f"Actualizados: {actualizados}."
            )
        )
