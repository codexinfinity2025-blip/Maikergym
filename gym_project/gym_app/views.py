from datetime import date
from decimal import Decimal, InvalidOperation
from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.cache import never_cache
from .security import limitar_acceso
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from gym_project.gym_app.models import (
    DiaSemanaChoice,
    Ejercicio,
    EstadoAsignacionChoice,
    EstadoSerieChoice,
    EstadoSesionChoice,
    ModalidadRutinaChoice,
    NivelEjercicioChoice,
    ObjetivoChoice,
    PerfilUsuario,
    RolChoice,
    SesionEntrenamiento,
)
from gym_project.gym_app.services import (
    asegurar_series_sesion,
    completar_ejercicio_sesion,
    completar_serie_entrenamiento,
    crear_rutina_automatica,
    crear_rutina_personalizada,
    iniciar_serie_entrenamiento,
    iniciar_sesion_entrenamiento,
    omitir_descanso_serie,
)
from gym_project.gym_app.wellness_content import (
    MENSAJES_MOTIVACIONALES,
    obtener_guia_nutricional,
    obtener_mensajes_del_dia,
)

DIETAS_POR_OBJETIVO = {
    'estetico': {
        'titulo': 'Dieta para objetivo estético',
        'descripcion': 'Plan balanceado para mejorar composición corporal, cuidar porciones y sostener energía durante el entrenamiento.',
    },
    'hipertrofia': {
        'titulo': 'Dieta para hipertrofia',
        'descripcion': 'Plan enfocado en suficiente proteína, carbohidratos de calidad y calorías controladas para apoyar el aumento muscular.',
    },
    'salud': {
        'titulo': 'Dieta para salud',
        'descripcion': 'Plan con alimentos variados, hidratación y hábitos sostenibles para mejorar bienestar general.',
    },
    'perder_peso': {
        'titulo': 'Dieta para pérdida de peso',
        'descripcion': 'Plan equilibrado para crear hábitos sostenibles, controlar porciones y acompañar el entrenamiento sin dietas extremas.',
    },
}


PREGUNTAS_NIVEL = [
    ("experiencia", "¿Cuánto tiempo llevas entrenando de forma constante?", [
        (0, "Menos de 3 meses"), (1, "Entre 3 y 12 meses"),
        (2, "Entre 1 y 3 años"), (3, "Más de 3 años"),
    ]),
    ("frecuencia", "¿Cuántas sesiones completas normalmente por semana?", [
        (0, "Una o ninguna"), (1, "Dos"), (2, "Tres o cuatro"), (3, "Cinco o más"),
    ]),
    ("tecnica", "¿Puedes mantener una técnica estable sin supervisión?", [
        (0, "Todavía estoy aprendiendo"), (1, "En ejercicios básicos"),
        (2, "En la mayoría"), (3, "Sí, y sé corregirme"),
    ]),
    ("cargas", "¿Cómo eliges el peso de trabajo?", [
        (0, "No sé calcularlo"), (1, "Uso un peso muy cómodo"),
        (2, "Dejo 2 o 3 repeticiones posibles"), (3, "Gestiono esfuerzo y progresión"),
    ]),
    ("progresion", "¿Registras pesos, repeticiones o tiempos?", [
        (0, "Nunca"), (1, "A veces"), (2, "Casi siempre"), (3, "Siempre y ajusto el plan"),
    ]),
    ("recuperacion", "¿Reconoces cuándo necesitas bajar la intensidad?", [
        (0, "No"), (1, "Con ayuda"), (2, "Generalmente"), (3, "Sí, con claridad"),
    ]),
    ("compuestos", "¿Qué tan familiar te resulta sentadilla, bisagra, empuje y tracción?", [
        (0, "Son nuevos para mí"), (1, "Conozco algunos"),
        (2, "Los ejecuto con control"), (3, "Los domino y sé adaptar variantes"),
    ]),
    ("consistencia", "En los últimos tres meses, ¿qué tan constante has sido?", [
        (0, "No he entrenado"), (1, "Intermitente"), (2, "Bastante constante"), (3, "Muy constante"),
    ]),
]


ORDEN_NIVELES = [
    NivelEjercicioChoice.PRINCIPIANTE,
    NivelEjercicioChoice.INTERMEDIO,
    NivelEjercicioChoice.ENCIMA_PROMEDIO,
    NivelEjercicioChoice.AVANZADO,
]

# Este listado corresponde a las demostraciones validadas e integradas en
# static/entrenador3d/entrenador.html. Un ejercicio nuevo queda en estado
# pendiente hasta que tenga una animación propia y revisada.
EJERCICIOS_CON_ANIMACION_3D = frozenset({
    "Sentadilla con barra",
    "Press de banca con barra",
    "Jalón al pecho en polea",
    "Prensa de piernas en máquina",
    "Peso muerto rumano con barra",
    "Hip thrust con barra",
    "Extensión de cuádriceps en máquina",
    "Curl femoral tumbado en máquina",
    "Abducción de cadera en máquina",
    "Elevación de talones de pie en máquina",
    "Press inclinado con mancuernas",
    "Aperturas de pecho en máquina",
    "Press militar sentado con mancuernas",
    "Elevaciones laterales con mancuernas",
    "Extensión de tríceps en polea",
    "Remo sentado en polea",
    "Remo inclinado con barra",
    "Dominadas asistidas en máquina",
    "Curl de bíceps con barra Z",
    "Curl martillo con mancuernas",
    "Plancha frontal sobre antebrazos",
    "Crunch abdominal en máquina",
    "Elevación de rodillas en silla romana",
    "Caminata del granjero con mancuernas",
    "Caminata inclinada en caminadora",
    "Remo en máquina ergométrica",
    "Sentadilla goblet con mancuerna",
    "Zancada estática con mancuernas",
    "Step-up al banco",
    "Puente de glúteos en suelo",
    "Press de pecho sentado en máquina",
    "Face pull en polea",
    "Curl de bíceps en polea baja",
    "Extensión de tríceps sobre la cabeza en polea",
    "Press Pallof en polea",
    "Bird dog",
})

def get_perfil(user):
    perfil, _ = PerfilUsuario.objects.get_or_create(user=user)
    return perfil


def calcular_edad(fecha_nacimiento):
    if not fecha_nacimiento:
        return None
    hoy = date.today()
    edad = hoy.year - fecha_nacimiento.year
    if (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day):
        edad -= 1
    return edad


def siguiente_paso_personalizacion(perfil):
    if not perfil.objetivo:
        return 'objetivo'
    if not perfil.nivel_declarado:
        return 'nivel_entrenamiento'
    if not perfil.prueba_nivel_completada or not perfil.nivel_entrenamiento:
        return 'prueba_nivel'
    if not perfil.configuracion_entrenamiento_completa:
        if perfil.modalidad_rutina == ModalidadRutinaChoice.PERSONALIZADA:
            return 'crear_rutina'
        return 'configurar_rutina'
    if not perfil.orientacion_nutricional_vista:
        return 'dieta'
    if not perfil.datos_completos:
        return 'datos_personales'
    return 'mi_entrenamiento'

def inicio(request):
    return render(request, 'inicio.html')

def escogenos(request):
    return render(request, 'escogenos.html')

def precios(request):
    return render(request, 'precios.html')

@require_http_methods(["GET", "POST"])
@sensitive_post_parameters('password', 'confirmar_password')
def registrarse(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        apellido = request.POST.get('apellido', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        confirmar_password = request.POST.get('confirmar_password', '')
        fecha_nacimiento_texto = request.POST.get(
            'fecha_nacimiento',
            '',
        ).strip()

        contexto = {
            'form_data': request.POST,
        }

        if password != confirmar_password:
            contexto['error'] = 'Las contraseñas no coinciden.'
            return render(request, 'registrarse.html', contexto)

        try:
            validate_email(email)
            validate_password(password, User(username=email, email=email, first_name=nombre, last_name=apellido))
        except ValidationError as error:
            contexto['error'] = ' '.join(error.messages)
            return render(request, 'registrarse.html', contexto)
        if User.objects.filter(email__iexact=email).exists() or User.objects.filter(username__iexact=email).exists():
            contexto['error'] = 'Ya existe una cuenta con ese correo.'
            return render(request, 'registrarse.html', contexto)

        try:
            fecha_nacimiento = date.fromisoformat(
                fecha_nacimiento_texto,
            )
        except ValueError:
            contexto['error'] = (
                'Ingresa una fecha de nacimiento válida.'
            )
            return render(request, 'registrarse.html', contexto)

        if fecha_nacimiento > date.today():
            contexto['error'] = (
                'La fecha de nacimiento no puede estar en el futuro.'
            )
            return render(request, 'registrarse.html', contexto)

        enfoque = request.POST.get('enfoque_corporal', 'full_body')
        if enfoque not in ('inferior', 'superior', 'full_body'):
            contexto['error'] = 'Selecciona un enfoque corporal válido.'
            return render(request, 'registrarse.html', contexto)
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=nombre,
            last_name=apellido,
        )
        perfil = get_perfil(user)
        perfil.enfoque_corporal = enfoque
        perfil.priorizar_tren_inferior = enfoque == 'inferior'
        perfil.fecha_nacimiento = fecha_nacimiento
        perfil.edad = calcular_edad(fecha_nacimiento)
        perfil.telefono = (
            request.POST.get('telefono', '').strip() or None
        )
        perfil.direccion = (
            request.POST.get('direccion', '').strip() or None
        )
        perfil.save(
            update_fields=[
                'fecha_nacimiento',
                'enfoque_corporal', 'priorizar_tren_inferior',
                'edad',
                'telefono',
                'direccion',
            ]
        )
        login(request, user)
        return redirect('objetivo')

    return render(request, 'registrarse.html')

def rutinas(request):
    return render(request, 'rutinas.html')

def salud(request):
    return render(request, 'salud.html')

def hipertrofia(request):
    return render(request, 'hipertrofia.html')

def estetico(request):
    return render(request, 'estetico.html')

def nutricion(request):
    return render(request, 'nutricion.html')

@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def objetivo(request):
    perfil = get_perfil(request.user)
    if request.method == 'POST':
        objetivo_elegido = request.POST.get('objetivo')
        if objetivo_elegido in DIETAS_POR_OBJETIVO:
            objetivo_cambio = (
                perfil.objetivo != objetivo_elegido
            )
            perfil.objetivo = objetivo_elegido
            if objetivo_cambio:
                perfil.configuracion_entrenamiento_completa = False
                perfil.orientacion_nutricional_vista = False
            perfil.save(
                update_fields=[
                    'objetivo',
                    'configuracion_entrenamiento_completa',
                    'orientacion_nutricional_vista',
                ]
            )
            return redirect('nivel_entrenamiento')
        return render(request, 'objetivo.html', {'error': 'Escoge un objetivo válido.'})
    return render(request, 'objetivo.html', {'perfil': perfil})


@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def nivel_entrenamiento_view(request):
    perfil = get_perfil(request.user)
    if not perfil.objetivo:
        return redirect('objetivo')

    if request.method == 'POST':
        nivel = request.POST.get('nivel')
        if nivel not in NivelEjercicioChoice.values:
            return render(request, 'nivel_entrenamiento.html', {
                'perfil': perfil,
                'niveles': NivelEjercicioChoice.choices,
                'error': 'Selecciona el nivel que mejor describa tu experiencia actual.',
            })
        perfil.nivel_declarado = nivel
        perfil.configuracion_entrenamiento_completa = False
        if nivel == NivelEjercicioChoice.PRINCIPIANTE:
            perfil.nivel_entrenamiento = nivel
            perfil.puntuacion_prueba_nivel = 0
            perfil.prueba_nivel_completada = True
        else:
            perfil.nivel_entrenamiento = None
            perfil.puntuacion_prueba_nivel = None
            perfil.prueba_nivel_completada = False
        perfil.save(update_fields=[
            'nivel_declarado', 'nivel_entrenamiento', 'puntuacion_prueba_nivel',
            'prueba_nivel_completada', 'configuracion_entrenamiento_completa',
        ])
        if perfil.prueba_nivel_completada:
            return redirect('configurar_rutina')
        return redirect('prueba_nivel')

    return render(request, 'nivel_entrenamiento.html', {
        'perfil': perfil,
        'niveles': NivelEjercicioChoice.choices,
    })


@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def prueba_nivel_view(request):
    perfil = get_perfil(request.user)
    if not perfil.objetivo:
        return redirect('objetivo')
    if not perfil.nivel_declarado:
        return redirect('nivel_entrenamiento')
    if perfil.nivel_declarado == NivelEjercicioChoice.PRINCIPIANTE:
        perfil.nivel_entrenamiento = NivelEjercicioChoice.PRINCIPIANTE
        perfil.prueba_nivel_completada = True
        perfil.save(update_fields=['nivel_entrenamiento', 'prueba_nivel_completada'])
        return redirect('configurar_rutina')

    contexto = {'perfil': perfil, 'preguntas': PREGUNTAS_NIVEL}
    if request.method == 'POST':
        respuestas = []
        for clave, _texto, _opciones in PREGUNTAS_NIVEL:
            try:
                valor = int(request.POST.get(clave, ''))
            except (TypeError, ValueError):
                valor = -1
            if valor not in (0, 1, 2, 3):
                contexto['error'] = 'Responde todas las preguntas para calcular tu nivel.'
                contexto['form_data'] = request.POST
                return render(request, 'prueba_nivel.html', contexto)
            respuestas.append(valor)

        puntuacion = sum(respuestas)
        if puntuacion <= 7:
            nivel_calculado = NivelEjercicioChoice.PRINCIPIANTE
        elif puntuacion <= 14:
            nivel_calculado = NivelEjercicioChoice.INTERMEDIO
        elif puntuacion <= 20:
            nivel_calculado = NivelEjercicioChoice.ENCIMA_PROMEDIO
        else:
            nivel_calculado = NivelEjercicioChoice.AVANZADO

        indice_declarado = ORDEN_NIVELES.index(perfil.nivel_declarado)
        indice_calculado = ORDEN_NIVELES.index(nivel_calculado)
        perfil.nivel_entrenamiento = ORDEN_NIVELES[min(indice_declarado, indice_calculado)]
        perfil.puntuacion_prueba_nivel = puntuacion
        perfil.prueba_nivel_completada = True
        perfil.configuracion_entrenamiento_completa = False
        perfil.save(update_fields=[
            'nivel_entrenamiento', 'puntuacion_prueba_nivel',
            'prueba_nivel_completada', 'configuracion_entrenamiento_completa',
        ])
        messages.success(
            request,
            f'Tu nivel recomendado es {perfil.get_nivel_entrenamiento_display()}.',
        )
        return redirect('configurar_rutina')

    return render(request, 'prueba_nivel.html', contexto)


def _normalizar_dias(valores):
    try:
        dias = sorted({int(valor) for valor in valores})
    except (TypeError, ValueError):
        return []
    if any(dia not in DiaSemanaChoice.values for dia in dias):
        return []
    return dias


@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def configurar_rutina_view(request):
    perfil = get_perfil(request.user)
    paso = siguiente_paso_personalizacion(perfil)
    if paso in ('objetivo', 'nivel_entrenamiento', 'prueba_nivel'):
        return redirect(paso)

    contexto = {
        'perfil': perfil,
        'dias_semana': DiaSemanaChoice.choices,
        'modalidades': ModalidadRutinaChoice.choices,
    }
    if request.method == 'POST':
        dias = _normalizar_dias(request.POST.getlist('dias'))
        modalidad = request.POST.get('modalidad')
        try:
            minutos = int(request.POST.get('minutos', ''))
            descanso = int(request.POST.get('descanso', ''))
        except (TypeError, ValueError):
            minutos = descanso = 0

        tiempos = {}
        for dia in dias:
            try:
                tiempos[str(dia)] = int(request.POST.get(f'minutos_dia_{dia}') or minutos)
            except (TypeError, ValueError):
                tiempos[str(dia)] = 0

        if not 1 <= len(dias) <= 6:
            contexto['error'] = 'Selecciona entre uno y seis días diferentes.'
        elif minutos < 45:
            contexto['error'] = 'El tiempo mínimo por entrenamiento es de 45 minutos.'
        elif any(valor < 45 for valor in tiempos.values()):
            contexto['error'] = 'Cada día elegido necesita al menos 45 minutos disponibles.'
        elif not 15 <= descanso <= 1800:
            contexto['error'] = 'El descanso debe estar entre 15 y 1800 segundos.'
        elif modalidad not in ModalidadRutinaChoice.values:
            contexto['error'] = 'Selecciona cómo deseas construir tu rutina.'
        else:
            perfil.dias_entrenamiento = dias
            genero_previo = request.POST.get('genero_previo')
            if genero_previo in ('femenino', 'masculino', 'otro'):
                perfil.genero = genero_previo
            enfoque = request.POST.get('enfoque_corporal', perfil.enfoque_corporal)
            if enfoque not in ('inferior', 'superior', 'full_body'):
                contexto['error'] = 'Selecciona un enfoque corporal válido.'
                return render(request, 'configurar_rutina.html', contexto)
            perfil.enfoque_corporal = enfoque
            perfil.priorizar_tren_inferior = enfoque == 'inferior'
            perfil.minutos_por_dia = tiempos
            perfil.duracion_sesion_minutos = minutos
            perfil.descanso_preferido_segundos = descanso
            perfil.modalidad_rutina = modalidad
            perfil.configuracion_entrenamiento_completa = False
            perfil.aviso_rutina_personalizada_aceptado = False
            perfil.save(update_fields=[
                'dias_entrenamiento', 'duracion_sesion_minutos', 'minutos_por_dia',
                'descanso_preferido_segundos', 'modalidad_rutina',
                'configuracion_entrenamiento_completa',
                'aviso_rutina_personalizada_aceptado',
                'genero', 'priorizar_tren_inferior', 'enfoque_corporal',
            ])
            if modalidad == ModalidadRutinaChoice.PERSONALIZADA:
                return redirect('crear_rutina')
            try:
                crear_rutina_automatica(
                    request.user, perfil.objetivo, perfil.nivel_entrenamiento,
                    dias, minutos, descanso, minutos_por_dia=tiempos,
                    priorizar_tren_inferior=perfil.priorizar_tren_inferior,
                    enfoque_corporal=perfil.enfoque_corporal,
                )
            except ValidationError as error:
                contexto['error'] = ' '.join(error.messages)
            else:
                perfil.configuracion_entrenamiento_completa = True
                perfil.save(update_fields=['configuracion_entrenamiento_completa'])
                return redirect('dieta')
        contexto['form_data'] = request.POST

    return render(request, 'configurar_rutina.html', contexto)


@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def crear_rutina_view(request):
    perfil = get_perfil(request.user)
    paso = siguiente_paso_personalizacion(perfil)
    if paso in ('objetivo', 'nivel_entrenamiento', 'prueba_nivel'):
        return redirect(paso)
    if perfil.modalidad_rutina != ModalidadRutinaChoice.PERSONALIZADA:
        return redirect('configurar_rutina')
    if not perfil.dias_entrenamiento:
        return redirect('configurar_rutina')

    contexto = {
        'perfil': perfil,
        'ejercicios': Ejercicio.objects.filter(activo=True).order_by('grupo_muscular', 'nombre'),
        'dias_elegidos': [
            {'numero': numero, 'valor': dia, 'nombre': DiaSemanaChoice(dia).label}
            for numero, dia in enumerate(perfil.dias_entrenamiento, start=1)
        ],
    }
    from .models import AsignacionPlanUsuario
    asignacion_actual = AsignacionPlanUsuario.objects.filter(usuario=request.user, estado='activo').first()
    filas_iniciales = []
    if asignacion_actual and asignacion_actual.plan.propietario_id == request.user.pk:
        for horario in asignacion_actual.horarios.filter(activo=True):
            if horario.dia_semana not in perfil.dias_entrenamiento:
                continue
            numero = perfil.dias_entrenamiento.index(horario.dia_semana) + 1
            fase = asignacion_actual.plan.fases.order_by('orden').first()
            if fase:
                dia_plan = fase.dias.filter(numero=horario.numero_dia_plan).first()
                if dia_plan:
                    for p in dia_plan.ejercicios_programados.filter(activo=True).order_by('orden'):
                        filas_iniciales.append({'dia': numero, 'ejercicio_id': p.ejercicio_id, 'series': p.series,
                            'cantidad': str(p.duracion_segundos or p.distancia_metros or p.repeticiones_max or 10), 'descanso': p.descanso_segundos})
    contexto['filas_iniciales'] = filas_iniciales
    contexto['editando'] = bool(filas_iniciales)
    if request.method == 'POST':
        contexto['filas_iniciales'] = [dict(zip(('dia', 'ejercicio_id', 'series', 'cantidad', 'descanso'), valores)) for valores in zip(*(request.POST.getlist(c) for c in ('dia', 'ejercicio_id', 'series', 'cantidad', 'descanso')))]
        if request.POST.get('acepta_aviso') != 'on':
            contexto['error'] = 'Debes confirmar que comprendes la advertencia de seguridad.'
            return render(request, 'crear_rutina.html', contexto)

        campos = {
            nombre: request.POST.getlist(nombre)
            for nombre in ('dia', 'ejercicio_id', 'series', 'cantidad', 'descanso')
        }
        total = len(campos['ejercicio_id'])
        if not total or any(len(valores) != total for valores in campos.values()):
            contexto['error'] = 'Revisa los ejercicios agregados a la rutina.'
            return render(request, 'crear_rutina.html', contexto)
        filas = [
            {nombre: valores[indice] for nombre, valores in campos.items()}
            for indice in range(total)
        ]
        try:
            crear_rutina_personalizada(
                request.user, perfil.objetivo, perfil.nivel_entrenamiento,
                perfil.dias_entrenamiento, filas,
            )
        except (ValidationError, ValueError, Ejercicio.DoesNotExist) as error:
            if isinstance(error, ValidationError):
                texto_error = ' '.join(error.messages)
            else:
                texto_error = 'Hay un valor inválido en la rutina. Revisa cada fila.'
            contexto['error'] = texto_error
            return render(request, 'crear_rutina.html', contexto)

        perfil.aviso_rutina_personalizada_aceptado = True
        perfil.configuracion_entrenamiento_completa = True
        perfil.save(update_fields=[
            'aviso_rutina_personalizada_aceptado',
            'configuracion_entrenamiento_completa',
        ])
        return redirect('dieta')

    return render(request, 'crear_rutina.html', contexto)

@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def dieta_view(request):
    perfil = get_perfil(request.user)
    if not perfil.objetivo:
        return redirect('objetivo')

    dieta = obtener_guia_nutricional(perfil.objetivo)

    if request.method == 'POST':
        perfil.orientacion_nutricional_vista = True
        perfil.dieta_aceptada = True
        perfil.save(update_fields=['orientacion_nutricional_vista', 'dieta_aceptada'])
        return redirect(siguiente_paso_personalizacion(perfil))

    return render(request, 'dieta.html', {
        'perfil': perfil,
        'dieta': dieta,
        'es_primera_configuracion': not perfil.orientacion_nutricional_vista,
    })


@login_required(login_url='login')
def notificaciones_view(request):
    from .models import AvisoSocial
    perfil = get_perfil(request.user)
    hoy = timezone.localdate()
    return render(request, 'notificaciones.html', {
        'perfil': perfil,
        'fecha_hoy': hoy,
        'notificaciones': list(reversed(perfil.mensajes_entregados)),
        'avisos_sociales': AvisoSocial.objects.filter(usuario=request.user).order_by('-creado')[:30],
    })


@login_required(login_url='login')
@require_http_methods(['POST'])
@transaction.atomic
def siguiente_mensaje_view(request):
    perfil = PerfilUsuario.objects.select_for_update().get(user=request.user)
    ahora = timezone.localtime()
    fecha = ahora.date().isoformat()
    historial = [m for m in perfil.mensajes_entregados if (ahora.date() - date.fromisoformat(m['fecha'])).days < 7]
    hoy = [m for m in historial if m['fecha'] == fecha]
    permitido = sum(ahora.hour >= hora for hora in (8, 14, 20))
    if request.POST.get('entrenando') == '1':
        permitido = max(1, permitido)
    mensaje = None
    # No acumular avisos al volver tarde ni lanzar tres al abrir una página.
    if len(hoy) < permitido and (not hoy or ahora.timestamp() - hoy[-1]['timestamp'] >= 3 * 3600):
        mensaje = {**obtener_mensajes_del_dia(request.user, perfil, ahora.date())[len(hoy)],
                   'fecha': fecha, 'timestamp': ahora.timestamp()}
        historial.append(mensaje)
        perfil.mensajes_entregados = historial
        perfil.save(update_fields=['mensajes_entregados'])
    return JsonResponse({'mensaje': mensaje})

@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def datos_personales_view(request):
    perfil = get_perfil(request.user)
    if not perfil.objetivo:
        return redirect('objetivo')
    if not perfil.nivel_declarado:
        return redirect('nivel_entrenamiento')
    if not perfil.prueba_nivel_completada or not perfil.nivel_entrenamiento:
        return redirect('prueba_nivel')
    if not perfil.configuracion_entrenamiento_completa:
        return redirect('configurar_rutina')
    if not perfil.orientacion_nutricional_vista:
        return redirect('dieta')
    if request.method == 'GET' and perfil.datos_completos:
        return redirect('mi_entrenamiento')

    if request.method == 'POST':
        perfil.genero = (
            request.POST.get('genero')
            or perfil.genero
            or None
        )
        peso_registro = request.POST.get('peso') or None
        try:
            altura = Decimal(request.POST.get('altura_cm') or str(perfil.altura_cm or '0'))
            peso_validado = Decimal(peso_registro or str(perfil.peso or '0'))
            if not altura.is_finite() or not peso_validado.is_finite() or not 50 <= altura <= 250 or not 1 <= peso_validado <= 500:
                raise ValueError()
            perfil.altura_cm = altura
        except (InvalidOperation, ValueError):
            return render(request, 'datos_personales.html', {'perfil': perfil, 'error': 'Revisa el peso y la altura en centímetros (50–250 cm).'})
        perfil.peso = peso_registro or perfil.peso
        if peso_registro and perfil.peso_inicial is None:
            perfil.peso_inicial = peso_registro

        fecha_nacimiento = request.POST.get('fecha_nacimiento') or None
        if fecha_nacimiento:
            try:
                perfil.fecha_nacimiento = date.fromisoformat(fecha_nacimiento)
                perfil.edad = calcular_edad(perfil.fecha_nacimiento)
            except ValueError:
                perfil.fecha_nacimiento = None
                perfil.edad = None
        elif perfil.fecha_nacimiento is not None:
            perfil.edad = calcular_edad(perfil.fecha_nacimiento)

        if request.FILES.get('foto'):
            perfil.foto = request.FILES['foto']

        if not perfil.genero or not perfil.peso or perfil.fecha_nacimiento is None:
            return render(request, 'datos_personales.html', {'perfil': perfil, 'error': 'Completa género, peso y fecha de nacimiento para continuar.'})

        perfil.datos_completos = True
        perfil.save()
        return redirect('mi_entrenamiento')

    return render(request, 'datos_personales.html', {'perfil': perfil})

def contacto(request):
    return render(request, 'contacto.html')

@require_http_methods(["GET", "POST"])
@sensitive_post_parameters('password')
@never_cache
@limitar_acceso
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        rol = request.POST.get('rol', 'usuario')

        try:
            user = User.objects.get(email__iexact=email)
            usuario_auth = authenticate(request, username=user.username, password=password)

            if usuario_auth:
                perfil = get_perfil(usuario_auth)
                if perfil.rol == rol or (rol == 'usuario' and perfil.rol == RolChoice.USUARIO):
                    login(request, usuario_auth)

                    if perfil.rol == RolChoice.ADMIN:
                        return redirect('panel_admin')
                    if perfil.rol == RolChoice.MODERADOR:
                        return redirect('panel_moderador')
                    return redirect(siguiente_paso_personalizacion(perfil))

                error = 'El rol no coincide con tu cuenta.'
            else:
                error = 'Correo o contraseña inválidos.'
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            User().set_password(password)
            error = 'Correo o contraseña inválidos.'

        return render(request, 'login.html', {'error': error})

    return render(request, 'login.html')


@login_required(login_url='login')
@sensitive_post_parameters('old_password', 'new_password1', 'new_password2')
@never_cache
@require_http_methods(['GET', 'POST'])
@limitar_acceso
def cambiar_password_view(request):
    form = PasswordChangeForm(request.user, request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        usuario = form.save()
        update_session_auth_hash(request, usuario)
        messages.success(request, 'Contraseña actualizada. Las otras sesiones deberán iniciar sesión nuevamente.')
        return redirect('cambiar_password')
    return render(request, 'cambiar_password.html', {'form': form})

@login_required(login_url='login')
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def cuenta_view(request):
    perfil = get_perfil(request.user)

    if perfil.rol == RolChoice.USUARIO and not perfil.personalizacion_completa():
        return redirect(siguiente_paso_personalizacion(perfil))

    if request.method == 'POST':
        accion = request.POST.get('accion')

        if accion == 'eliminar_cuenta':
            if not request.user.check_password(request.POST.get('password_actual', '')):
                return JsonResponse({'ok': False, 'error': 'Confirma tu contraseña actual para eliminar la cuenta.'}, status=400)
            user = request.user
            from django.db.models.deletion import ProtectedError
            try:
                with transaction.atomic():
                    user.delete()
            except ProtectedError:
                return JsonResponse({'ok': False, 'error': 'La cuenta tiene registros protegidos o administra un grupo. Contacta al administrador para gestionar su eliminación sin perder el historial compartido.'}, status=409)
            logout(request)
            return redirect('inicio')

        if accion in ['actualizar_cuenta', 'actualizar_foto']:
            if request.FILES.get('foto'):
                perfil.foto = request.FILES['foto']

            if accion == 'actualizar_cuenta':
                if request.POST.get('altura_cm'):
                    try:
                        altura = Decimal(request.POST['altura_cm'])
                        if not altura.is_finite() or not 50 <= altura <= 250:
                            raise ValueError()
                        perfil.altura_cm = altura
                    except (InvalidOperation, ValueError):
                        return JsonResponse({'ok': False, 'error': 'Altura inválida: utiliza centímetros entre 50 y 250.'}, status=400)
                nombre_completo = request.POST.get('nombre', '').strip()
                if nombre_completo:
                    partes = nombre_completo.split()
                    request.user.first_name = partes[0]
                    request.user.last_name = ' '.join(partes[1:])

                email = request.POST.get('email', '').strip().lower()
                if email and email != request.user.email.lower():
                    try:
                        validate_email(email)
                    except ValidationError:
                        return JsonResponse({'ok': False, 'error': 'Correo inválido.'}, status=400)
                    if not request.user.check_password(request.POST.get('password_actual', '')):
                        return JsonResponse({'ok': False, 'error': 'Introduce tu contraseña actual para cambiar el correo.'}, status=400)
                    if User.objects.exclude(pk=request.user.pk).filter(email__iexact=email).exists() or User.objects.exclude(pk=request.user.pk).filter(username__iexact=email).exists():
                        return JsonResponse({'ok': False, 'error': 'No se puede utilizar ese correo.'}, status=400)
                if email:
                    request.user.email = email
                    request.user.username = email

                perfil.telefono = request.POST.get('telefono', '').strip() or None
                perfil.direccion = request.POST.get('direccion', '').strip() or None
                perfil.peso_inicial = request.POST.get('peso_inicial') or perfil.peso_inicial or perfil.peso
                perfil.peso = request.POST.get('peso') or perfil.peso

                request.user.save()

            perfil.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'ok': True, 'foto_url': perfil.foto.url if perfil.foto else ''})
            return redirect('cuenta')

    peso_inicial = perfil.peso_inicial or perfil.peso
    context = {
        'perfil': perfil,
        'peso_inicial_value': f'{peso_inicial:.2f}' if peso_inicial is not None else '',
        'peso_actual_value': f'{perfil.peso:.2f}' if perfil.peso is not None else '',
    }
    return render(request, 'cuenta.html', context)
@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def mi_entrenamiento_view(request):
    perfil = get_perfil(request.user)

    if (
        perfil.rol == RolChoice.USUARIO
        and not perfil.personalizacion_completa()
    ):
        return redirect(
            siguiente_paso_personalizacion(perfil)
        )

    asignacion = (
        request.user.planes_asignados
        .filter(
            estado=EstadoAsignacionChoice.ACTIVO,
        )
        .select_related("plan")
        .prefetch_related("horarios")
        .first()
    )

    context = {
        "perfil": perfil,
        "asignacion": asignacion,
        "fase_actual": None,
        "semana_actual": None,
        "calendario_semana": [],
        "horario_hoy": None,
        "dia_hoy": None,
        "ejercicios_hoy": [],
        "sesion_hoy": None,
        "fecha_hoy": timezone.localdate(),
    }

    if asignacion is None:
        return render(
            request,
            "mi_entrenamiento.html",
            context,
        )

    fase_actual = asignacion.fase_actual
    hoy = timezone.localdate()

    dias_fase = {}

    if fase_actual is not None:
        dias_fase = {
            dia.numero: dia
            for dia in (
                fase_actual.dias
                .filter(activo=True)
                .prefetch_related(
                    "ejercicios_programados__ejercicio"
                )
            )
        }

    horarios = sorted(
        [
            horario
            for horario in asignacion.horarios.all()
            if horario.activo
        ],
        key=lambda horario: horario.dia_semana,
    )

    calendario_semana = [
        {
            "horario": horario,
            "dia_plan": dias_fase.get(
                horario.numero_dia_plan
            ),
        }
        for horario in horarios
    ]

    horario_hoy = next(
        (
            horario
            for horario in horarios
            if horario.dia_semana == hoy.weekday()
        ),
        None,
    )

    dia_hoy = None
    ejercicios_hoy = []

    if horario_hoy is not None:
        dia_hoy = dias_fase.get(
            horario_hoy.numero_dia_plan
        )

    if dia_hoy is not None:
        ejercicios_hoy = [
            ejercicio_programado
            for ejercicio_programado
            in dia_hoy.ejercicios_programados.all()
            if (
                ejercicio_programado.activo
                and ejercicio_programado.ejercicio.activo
            )
        ]

    if request.method == "POST":
        accion = request.POST.get("accion")

        if accion == "iniciar_sesion":
            if dia_hoy is None:
                messages.error(
                    request,
                    "Hoy no tienes un entrenamiento programado.",
                )
            else:
                try:
                    sesion, sesion_creada = (
                        iniciar_sesion_entrenamiento(
                            asignacion,
                            dia_hoy,
                        )
                    )
                except ValidationError as error:
                    messages.error(
                        request,
                        " ".join(error.messages),
                    )
                else:
                    if sesion_creada:
                        messages.success(
                            request,
                            "Entrenamiento iniciado correctamente.",
                        )
                    else:
                        messages.success(
                            request,
                            "Tu entrenamiento ya estaba iniciado.",
                        )

                    return redirect(
                        "reproductor_entrenamiento",
                        sesion_id=sesion.pk,
                    )

        elif accion == "completar_ejercicio":
            try:
                registro, puntos_entregados, sesion = (
                    completar_ejercicio_sesion(
                        usuario=request.user,
                        ejercicio_sesion_id=request.POST.get(
                            "ejercicio_sesion_id"
                        ),
                        series_completadas=request.POST.get(
                            "series_completadas"
                        ),
                        repeticiones_realizadas=request.POST.get(
                            "repeticiones_realizadas"
                        ),
                        duracion_realizada_segundos=request.POST.get(
                            "duracion_realizada_segundos"
                        ),
                        distancia_realizada_metros=request.POST.get(
                            "distancia_realizada_metros"
                        ),
                        peso_utilizado_kg=request.POST.get(
                            "peso_utilizado_kg"
                        ),
                        observaciones=request.POST.get(
                            "observaciones",
                            "",
                        ),
                    )
                )
            except ValidationError as error:
                messages.error(
                    request,
                    " ".join(error.messages),
                )
            else:
                if puntos_entregados:
                    messages.success(
                        request,
                        (
                            "Ejercicio completado. Ganaste "
                            f"{registro.puntos_obtenidos} puntos."
                        ),
                    )
                else:
                    messages.info(
                        request,
                        "Este ejercicio ya estaba completado.",
                    )

        else:
            messages.error(
                request,
                "La acción solicitada no es válida.",
            )

        return redirect("mi_entrenamiento")

    sesion_hoy = None

    if dia_hoy is not None:
        sesion_hoy = (
            asignacion.sesiones
            .filter(
                semana_plan=asignacion.semana_actual,
                dia_plan=dia_hoy,
            )
            .prefetch_related(
                "ejercicios__ejercicio_programado__ejercicio"
            )
            .first()
        )

        registros_por_programado = {}

    if sesion_hoy is not None:
        registros_por_programado = {
            registro.ejercicio_programado_id: registro
            for registro in sesion_hoy.ejercicios.all()
        }

    for programado in ejercicios_hoy:
        programado.registro_sesion = (
            registros_por_programado.get(
                programado.id
            )
        )

    context.update({
        "fase_actual": fase_actual,
        "semana_actual": asignacion.semana_actual,
        "calendario_semana": calendario_semana,
        "horario_hoy": horario_hoy,
        "dia_hoy": dia_hoy,
        "ejercicios_hoy": ejercicios_hoy,
        "sesion_hoy": sesion_hoy,
    })

    return render(
        request,
        "mi_entrenamiento.html",
        context,
    )


@login_required(login_url="login")
@require_http_methods(["GET", "POST"])
def reproductor_entrenamiento_view(request, sesion_id):
    sesion = (
        SesionEntrenamiento.objects
        .filter(
            pk=sesion_id,
            asignacion__usuario=request.user,
        )
        .select_related(
            "asignacion__plan",
            "dia_plan__fase",
        )
        .first()
    )

    if sesion is None:
        messages.error(
            request,
            "No se encontró el entrenamiento solicitado.",
        )
        return redirect("mi_entrenamiento")

    asegurar_series_sesion(sesion)

    if request.method == "POST":
        accion = request.POST.get("accion", "")
        serie_id = request.POST.get("serie_id")

        try:
            if not str(serie_id or "").isdigit():
                raise ValidationError(
                    "La serie seleccionada no es válida."
                )

            from .models import SerieEjercicioSesion
            if not SerieEjercicioSesion.objects.filter(pk=serie_id, ejercicio_sesion__sesion=sesion).exists():
                raise ValidationError('La serie no pertenece a este entrenamiento.')

            if accion == "iniciar_serie":
                serie, iniciada = iniciar_serie_entrenamiento(
                    usuario=request.user,
                    serie_id=serie_id,
                )

                if iniciada:
                    messages.success(
                        request,
                        f"Serie {serie.numero} iniciada.",
                    )
                else:
                    messages.info(
                        request,
                        "La serie ya estaba en progreso.",
                    )

            elif accion == "completar_serie":
                serie, guardada, registro, sesion = (
                    completar_serie_entrenamiento(
                        usuario=request.user,
                        serie_id=serie_id,
                        repeticiones_realizadas=request.POST.get(
                            "repeticiones_realizadas"
                        ),
                        duracion_realizada_segundos=request.POST.get(
                            "duracion_realizada_segundos"
                        ),
                        distancia_realizada_metros=request.POST.get(
                            "distancia_realizada_metros"
                        ),
                        peso_utilizado_kg=request.POST.get(
                            "peso_utilizado_kg"
                        ),
                    )
                )

                if not guardada:
                    messages.info(
                        request,
                        "Esta serie ya estaba completada.",
                    )
                elif sesion.estado == EstadoSesionChoice.COMPLETADA:
                    messages.success(
                        request,
                        "¡Entrenamiento completado! "
                        f"Ganaste {sesion.puntos_obtenidos} puntos.",
                    )
                elif registro.completado:
                    messages.success(
                        request,
                        "Ejercicio completado. "
                        f"Ganaste {registro.puntos_obtenidos} puntos.",
                    )
                else:
                    messages.success(
                        request,
                        f"Serie {serie.numero} completada.",
                    )

            elif accion == "omitir_descanso":
                serie, omitido = omitir_descanso_serie(
                    usuario=request.user,
                    serie_id=serie_id,
                )

                if omitido:
                    messages.info(
                        request,
                        "Descanso omitido. Puedes continuar.",
                    )
                else:
                    messages.info(
                        request,
                        "El descanso ya había terminado.",
                    )

            else:
                raise ValidationError(
                    "La acción solicitada no es válida."
                )

        except ValidationError as error:
            messages.error(
                request,
                " ".join(error.messages),
            )

        return redirect(
            "reproductor_entrenamiento",
            sesion_id=sesion.pk,
        )

    ejercicios_sesion = list(
        sesion.ejercicios
        .filter(
            ejercicio_programado__activo=True,
            ejercicio_programado__ejercicio__activo=True,
        )
        .select_related(
            "ejercicio_programado__ejercicio",
        )
        .prefetch_related("series")
        .order_by("ejercicio_programado__orden")
    )

    series_reproductor = []

    for registro in ejercicios_sesion:
        registro.series_ordenadas = list(
            registro.series.all()
        )
        series_reproductor.extend(
            registro.series_ordenadas
        )

    serie_en_progreso = next(
        (
            serie
            for serie in series_reproductor
            if serie.estado == EstadoSerieChoice.EN_PROGRESO
        ),
        None,
    )
    primera_pendiente = next(
        (
            serie
            for serie in series_reproductor
            if serie.estado == EstadoSerieChoice.PENDIENTE
        ),
        None,
    )
    serie_actual = serie_en_progreso or primera_pendiente
    ejercicio_actual = (
        serie_actual.ejercicio_sesion
        if serie_actual is not None
        else None
    )

    ultima_completada = next(
        (
            serie
            for serie in reversed(series_reproductor)
            if serie.estado == EstadoSerieChoice.COMPLETADA
        ),
        None,
    )
    ahora = timezone.now()
    descanso_activo = bool(
        serie_actual is not None
        and serie_en_progreso is None
        and ultima_completada is not None
        and ultima_completada.descanso_hasta is not None
        and not ultima_completada.descanso_omitido
        and ultima_completada.descanso_hasta > ahora
    )
    segundos_descanso = 0

    if descanso_activo:
        segundos_descanso = (
            int(
                (
                    ultima_completada.descanso_hasta - ahora
                ).total_seconds()
            )
            + 1
        )

    total_series = len(series_reproductor)
    series_completadas = sum(
        1
        for serie in series_reproductor
        if serie.estado == EstadoSerieChoice.COMPLETADA
    )
    progreso_porcentaje = (
        round(series_completadas * 100 / total_series)
        if total_series
        else 0
    )

    numero_ejercicio = None
    siguiente_ejercicio = None

    if ejercicio_actual is not None:
        for indice, registro in enumerate(
            ejercicios_sesion,
            start=1,
        ):
            if registro.pk == ejercicio_actual.pk:
                numero_ejercicio = indice

                if indice < len(ejercicios_sesion):
                    siguiente_ejercicio = ejercicios_sesion[indice]

                break

    context = {
        "perfil": get_perfil(request.user),
        "sesion": sesion,
        "ejercicios_sesion": ejercicios_sesion,
        "ejercicio_actual": ejercicio_actual,
        "serie_actual": serie_actual,
        "serie_en_progreso": serie_en_progreso,
        "ultima_serie_completada": ultima_completada,
        "descanso_activo": descanso_activo,
        "segundos_descanso": segundos_descanso,
        "series_completadas": series_completadas,
        "total_series": total_series,
        "progreso_porcentaje": progreso_porcentaje,
        "numero_ejercicio": numero_ejercicio,
        "total_ejercicios": len(ejercicios_sesion),
        "siguiente_ejercicio": siguiente_ejercicio,
        "modelo_3d_disponible": bool(
            ejercicio_actual
            and ejercicio_actual.ejercicio_programado.ejercicio.nombre
            in EJERCICIOS_CON_ANIMACION_3D
        ),
    }

    return render(
        request,
        "reproductor_entrenamiento.html",
        context,
    )


@login_required(login_url='login')
def panel_moderador_view(request):
    try:
        perfil = get_perfil(request.user)
        if perfil.rol not in [RolChoice.MODERADOR, RolChoice.ADMIN]:
            return HttpResponseForbidden('No tienes permiso para acceder a esta página.')
    except PerfilUsuario.DoesNotExist:
        return HttpResponseForbidden('No tienes permiso para acceder a esta página.')

    context = {'perfil': perfil}
    return render(request, 'panel_moderador.html', context)

@login_required(login_url='login')
def panel_admin_view(request):
    try:
        perfil = get_perfil(request.user)
        if perfil.rol != RolChoice.ADMIN:
            return HttpResponseForbidden('No tienes permiso para acceder a esta página.')
    except PerfilUsuario.DoesNotExist:
        return HttpResponseForbidden('No tienes permiso para acceder a esta página.')

    context = {'perfil': perfil}
    return render(request, 'panel_admin.html', context)
