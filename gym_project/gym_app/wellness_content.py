import random
from .meal_suggestions import comidas_del_dia


NUTRICION_POR_OBJETIVO = {
    "hipertrofia": {
        "titulo": "Nutrición para apoyar el crecimiento muscular",
        "descripcion": (
            "Entrenar estimula el músculo; una alimentación variada aporta la "
            "energía y los nutrientes que el cuerpo utiliza para recuperarse."
        ),
        "principios": [
            "Incluye una fuente de proteína en las comidas principales.",
            "Combina carbohidratos sencillos de preparar alrededor del entrenamiento.",
            "Mantén frutas, verduras, agua y horarios sostenibles.",
        ],
        "dias": [
            ("Lunes", "Avena con leche, banano y maní", "Arroz con pollo y ensalada de aguacate", "Yogur natural con fruta", "Arepa con huevos revueltos y tomate"),
            ("Martes", "Huevos con pan integral y papaya", "Pasta con carne magra y verduras", "Batido de leche, avena y cacao", "Bowl de fríjoles, arroz y queso fresco"),
            ("Miércoles", "Yogur con granola casera y mango", "Lentejas con arroz, huevo y ensalada", "Sándwich de atún y pepino", "Pollo salteado con papa y verduras"),
            ("Jueves", "Arepa con queso y huevos", "Arroz salteado con pollo y vegetales", "Fruta con yogur o kumis", "Tortilla de papa con ensalada"),
            ("Viernes", "Avena fría con yogur y fresas", "Carne molida magra con puré y ensalada", "Pan integral con crema de maní", "Wrap de pollo, fríjoles y vegetales"),
            ("Sábado", "Calentado de arroz y fríjoles con huevo", "Pescado a la plancha con papa y ensalada", "Batido de yogur y banano", "Pasta corta con atún y tomate"),
            ("Domingo", "Tostadas con huevo, queso y fruta", "Pollo al horno con arroz y verduras", "Yogur con avena y semillas", "Crema de verduras con sándwich de pavo"),
        ],
    },
    "perder_peso": {
        "titulo": "Nutrición ligera, sabrosa y sostenible",
        "descripcion": (
            "La pérdida de peso sostenible se apoya en porciones conscientes, "
            "alimentos saciantes y constancia, sin convertir cada comida en un castigo."
        ),
        "principios": [
            "Prioriza verduras, frutas enteras, legumbres y proteínas magras.",
            "Usa preparaciones al horno, a la plancha, cocidas o salteadas.",
            "Come despacio y ajusta la porción a tu hambre real.",
        ],
        "dias": [
            ("Lunes", "Huevos con tomate y una arepa pequeña", "Pollo a la plancha con ensalada y papa", "Manzana con un puñado de maní", "Crema de ahuyama con queso fresco"),
            ("Martes", "Yogur natural con fruta y avena", "Bowl de lentejas, verduras y arroz", "Pepino y zanahoria con hummus", "Tortilla de vegetales con aguacate"),
            ("Miércoles", "Avena con canela, leche y banano", "Pescado con ensalada fresca y yuca cocida", "Yogur o fruta de temporada", "Wrap de pollo con muchas verduras"),
            ("Jueves", "Tostada integral con huevo y aguacate", "Carne magra salteada con verduras y arroz", "Palomitas caseras sin exceso de aceite", "Ensalada tibia de garbanzos y huevo"),
            ("Viernes", "Batido espeso de yogur, fruta y avena", "Fríjoles con ensalada y porción moderada de arroz", "Mandarina con queso fresco", "Sopa de pollo con verduras"),
            ("Sábado", "Arepa pequeña con queso y fruta", "Pollo al horno con vegetales y papa criolla", "Fruta picada con limón", "Atún con maíz, tomate y galletas integrales"),
            ("Domingo", "Huevos pericos con pan integral", "Pasta con salsa de tomate, atún y ensalada", "Yogur con semillas", "Bowl de verduras salteadas, arroz y huevo"),
        ],
    },
    "estetico": {
        "titulo": "Nutrición para composición corporal y energía",
        "descripcion": (
            "Una apariencia atlética se construye con entrenamiento, recuperación y "
            "comidas consistentes que ayuden a conservar músculo y controlar porciones."
        ),
        "principios": [
            "Busca equilibrio: proteína, vegetales, carbohidrato y grasa saludable.",
            "Prefiere hábitos repetibles antes que restricciones extremas.",
            "Ajusta las cantidades según tu energía, progreso y entrenamiento.",
        ],
        "dias": [
            ("Lunes", "Omelette de vegetales con arepa", "Pollo, arroz, ensalada y aguacate", "Yogur con mango", "Tacos caseros de carne magra y vegetales"),
            ("Martes", "Avena con cacao, banano y semillas", "Pescado con papa y ensalada de repollo", "Fruta con queso fresco", "Bowl de garbanzos, huevo y verduras"),
            ("Miércoles", "Tostadas con huevo y tomate", "Pasta con pollo y vegetales", "Batido de yogur y frutos rojos", "Crema de verduras con sándwich de atún"),
            ("Jueves", "Yogur con avena, piña y maní", "Lentejas con arroz y ensalada", "Arepa pequeña con queso", "Pollo salteado con verduras y papa"),
            ("Viernes", "Arepa con huevos pericos y fruta", "Carne magra, puré y ensalada", "Manzana con crema de maní", "Wrap de pavo, aguacate y vegetales"),
            ("Sábado", "Calentado sencillo con huevo", "Arroz con pollo casero y ensalada", "Yogur con granola", "Tortilla española ligera con tomate"),
            ("Domingo", "Pan integral con queso, huevo y fruta", "Pescado al horno con yuca y ensalada", "Batido de leche y banano", "Sopa de verduras con pollo desmechado"),
        ],
    },
    "salud": {
        "titulo": "Nutrición cotidiana para sentirte mejor",
        "descripcion": (
            "Comer bien no exige platos complicados. La variedad, la hidratación y "
            "los horarios razonables ayudan a entrenar con energía y recuperarte."
        ),
        "principios": [
            "Incluye colores distintos de frutas y verduras durante la semana.",
            "Alterna huevos, pollo, pescado, lácteos y legumbres.",
            "Mantén agua disponible y disfruta la comida sin culpa.",
        ],
        "dias": [
            ("Lunes", "Avena con fruta y canela", "Arroz, pollo, ensalada y aguacate", "Yogur con semillas", "Sopa de verduras con huevo"),
            ("Martes", "Huevos con arepa y papaya", "Lentejas con arroz y ensalada", "Banano con maní", "Sándwich integral de atún y tomate"),
            ("Miércoles", "Yogur con avena y mango", "Pescado con papa y vegetales", "Fruta de temporada", "Tortilla de vegetales con queso"),
            ("Jueves", "Tostada integral con aguacate y huevo", "Pasta con pollo y verduras", "Palomitas caseras y fruta", "Crema de ahuyama con pan integral"),
            ("Viernes", "Batido de leche, avena y banano", "Fríjoles con arroz y ensalada fresca", "Yogur natural", "Wrap de pollo y vegetales"),
            ("Sábado", "Arepa con queso y huevos pericos", "Carne magra salteada con papa y verduras", "Fruta picada", "Bowl de garbanzos, tomate y huevo"),
            ("Domingo", "Calentado pequeño con huevo", "Pollo al horno con arroz y ensalada", "Queso fresco con fruta", "Sopa casera de pollo y verduras"),
        ],
    },
}


MENSAJES_MOTIVACIONALES = [
    "{nombre}, hoy no necesitas hacerlo perfecto: solo necesitas empezar.",
    "Tu objetivo de {objetivo} se construye con decisiones pequeñas como la de hoy.",
    "Entrena con calma, cuida la técnica y deja que la constancia haga su trabajo.",
    "Cada repetición controlada es una inversión en tu versión más fuerte.",
    "No compitas con nadie: tu referencia es la persona que eras ayer.",
    "Un día difícil también cuenta cuando decides presentarte y hacer lo posible.",
    "Tu cuerpo aprende con paciencia; dale movimientos limpios y tiempo para adaptarse.",
    "La motivación inicia el camino, pero el hábito es quien te lleva más lejos.",
    "Hoy puede ser el entrenamiento que te recuerde de qué eres capaz.",
    "Avanzar lento sigue siendo avanzar, {nombre}.",
    "La fuerza también se nota cuando eliges descansar y volver con energía.",
    "Concéntrate en una serie a la vez; el resultado completo llegará después.",
    "Respira, ajusta tu postura y confía en el proceso que estás construyendo.",
    "Tu progreso no desaparece por tener un día menos intenso.",
    "Moverte hoy es una forma de cuidar a tu yo del futuro.",
    "Una buena técnica vale más que levantar un peso que todavía no controlas.",
    "La disciplina no exige perfección; exige volver a intentarlo.",
    "Celebra que estás aquí: muchas metas comienzan exactamente así.",
    "Tu ritmo es válido siempre que te permita avanzar de forma segura.",
    "La energía cambia, pero tu compromiso puede mantenerse.",
    "Haz que la última repetición se vea tan limpia como la primera.",
    "Cada descanso prepara una mejor serie; úsalo con intención.",
    "{nombre}, escucha tu cuerpo sin abandonar tu propósito.",
    "Hoy trabaja con paciencia; mañana agradecerás haber sido constante.",
    "No subestimes veinte minutos de enfoque: pueden cambiar todo tu día.",
    "El entrenamiento es una conversación con tu cuerpo, no un castigo.",
    "Tu objetivo merece esfuerzo, pero también cuidado y buenos hábitos.",
    "La confianza crece cuando cumples las promesas pequeñas que te haces.",
    "No necesitas sentirte imparable; basta con dar el siguiente paso.",
    "Técnica primero, intensidad después y progreso durante mucho tiempo.",
    "El mejor entrenamiento es el que puedes repetir sin lastimarte.",
    "Hoy suma una victoria sencilla: completar lo planeado con atención.",
    "El cuerpo cambia cuando la constancia deja de depender del ánimo.",
    "Tu sesión de hoy cuenta, incluso si necesitas adaptar el ritmo.",
    "Mantén la mirada en el proceso: allí ocurren los cambios reales.",
    "Entrenar también es aprender a conocerte y respetar tus límites.",
    "La recuperación, el agua y una buena comida también forman parte del plan.",
    "Hazlo por cómo quieres sentirte, no solo por cómo quieres verte.",
    "Cada semana consistente pesa más que un único día extraordinario.",
    "El progreso silencioso sigue siendo progreso.",
    "{nombre}, convierte la intención de hoy en una acción concreta.",
    "Ajustar un ejercicio no es rendirse; es entrenar con inteligencia.",
    "Tu fuerza no se mide solo en kilos, también en perseverancia.",
    "Comienza suave, encuentra el control y termina con orgullo.",
    "El esfuerzo de hoy está enseñando a tu cuerpo a responder mejor mañana.",
    "Dale a cada movimiento un propósito y a cada descanso su espacio.",
    "No apresures los resultados que quieres conservar por mucho tiempo.",
    "Hoy tienes otra oportunidad para acercarte a {objetivo}.",
    "Una rutina sostenible siempre supera una promesa imposible.",
    "Tu bienestar es una meta diaria, no una recompensa distante.",
    "Cuando aparezca la duda, vuelve a lo básico: respira y ejecuta con control.",
    "Los hábitos fuertes nacen de repetir acciones simples.",
    "La consistencia se construye incluso en los días en que haces menos.",
    "Tu cuerpo merece que entrenes con ambición y también con respeto.",
    "No busques una sesión perfecta; busca una sesión consciente.",
    "La paciencia también es parte del entrenamiento.",
    "Hoy enfócate en sentir el músculo correcto, no en mover el mayor peso.",
    "Un paso bien dado vale más que tres pasos apresurados.",
    "Descansar entre series no rompe el ritmo: lo sostiene.",
    "{nombre}, la mejor prueba de progreso es seguir apareciendo.",
    "Tu plan se adapta a ti; no tienes que adaptarte a expectativas ajenas.",
    "La postura estable es el punto de partida de una repetición poderosa.",
    "Tu meta de {objetivo} necesita semanas honestas, no atajos.",
    "Entrena para sentirte capaz dentro y fuera del gimnasio.",
    "Si hoy cuesta, reduce la velocidad y conserva la intención.",
    "Reconoce lo que ya has avanzado antes de exigirte el siguiente nivel.",
    "Cada sesión completa fortalece algo más que tus músculos.",
    "Hoy practica la versión del hábito que quieres conservar mañana.",
    "Termina con energía suficiente para querer regresar.",
    "Tu progreso es personal, real y merece tiempo.",
]


def obtener_mensajes_del_dia(usuario, perfil, fecha):
    nombre = usuario.first_name.strip() or "Atleta"
    objetivo = perfil.get_objetivo_display().lower() if perfil.objetivo else "sentirte mejor"
    biblioteca = list(MENSAJES_MOTIVACIONALES)
    random.Random(f"maikergym:{usuario.pk}").shuffle(biblioteca)
    inicio = (fecha.toordinal() * 3) % len(biblioteca)
    elegidos = [
        biblioteca[(inicio + desplazamiento) % len(biblioteca)]
        for desplazamiento in range(3)
    ]
    momentos = ("Para comenzar el día", "Impulso de mediodía", "Para cerrar con intención")
    return [
        {
            "momento": momento,
            "mensaje": mensaje.format(nombre=nombre, objetivo=objetivo),
        }
        for momento, mensaje in zip(momentos, elegidos)
    ]


def obtener_guia_nutricional(objetivo):
    guia = NUTRICION_POR_OBJETIVO.get(objetivo, NUTRICION_POR_OBJETIVO["salud"])
    return {
        **guia,
        "dias": [
            {
                "nombre": dia[0],
                "comidas": comidas_del_dia(indice, objetivo),
                "desayuno": dia[1],
                "almuerzo": dia[2],
                "merienda": dia[3],
                "cena": dia[4],
            }
            for indice, dia in enumerate(guia["dias"])
        ],
    }
