from datetime import date, timedelta
import logging
from .profile_validation import (
    REFERENCIAS_GRASA_VISUAL,
    estimar_grasa_navy,
    validar_fecha_nacimiento,
)
from .routine_edit import proteger_sesion_en_curso
from django.db import transaction, IntegrityError
from django.db.models import Case, IntegerField, Value, When, Q
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
    GeneroChoice,
    EstadoAsignacionChoice,
    EstadoSerieChoice,
    EstadoSesionChoice,
    ModalidadRutinaChoice,
    NivelEjercicioChoice,
    MetodoGrasaChoice,
    ObjetivoChoice,
    PerfilUsuario,
    RolChoice,
    SesionEntrenamiento,
    TipoDocumentoChoice,
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

logger = logging.getLogger(__name__)

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
    hoy = timezone.localdate()
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

@require_http_methods(["GET", "POST"])
def precios(request):
    if request.method == 'POST':
        elegido = request.POST.get('plan_precio', '')
        if elegido not in ('mensual', 'semestral', 'premium_anual'):
            return JsonResponse({'error': 'Plan no válido.'}, status=400)
        if request.user.is_authenticated:
            perfil = get_perfil(request.user)
            perfil.plan_precio = elegido
            perfil.save(update_fields=['plan_precio'])
            return redirect('cuenta')
        request.session['plan_precio_pendiente'] = elegido
        return redirect('registrarse')
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
            'enfoque_actual': request.POST.get('enfoque_corporal', 'full_body'),
        }

        if not nombre or not apellido:
            contexto['error'] = 'Completa tu nombre y apellido para continuar.'
            return render(request, 'registrarse.html', contexto)
        campos = (
            (nombre, User._meta.get_field('first_name').max_length, 'Nombre'),
            (apellido, User._meta.get_field('last_name').max_length, 'Apellido'),
            (email, User._meta.get_field('username').max_length, 'Correo'),
            (request.POST.get('documento', '').strip(), PerfilUsuario._meta.get_field('documento').max_length, 'Documento'),
            (request.POST.get('telefono', '').strip(), PerfilUsuario._meta.get_field('telefono').max_length, 'Teléfono'),
            (request.POST.get('direccion', '').strip(), PerfilUsuario._meta.get_field('direccion').max_length, 'Dirección'),
        )
        for valor, limite, etiqueta in campos:
            if len(valor) > limite:
                contexto['error'] = f'{etiqueta}: utiliza como máximo {limite} caracteres.'
                return render(request, 'registrarse.html', contexto)

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
            fecha_nacimiento = validar_fecha_nacimiento(
                fecha_nacimiento_texto,
            )
        except ValidationError as error:
            contexto['error'] = error.messages[0]
            return render(request, 'registrarse.html', contexto)

        if calcular_edad(fecha_nacimiento) < 18 and request.POST.get('autorizacion_menor') != 'on':
            contexto['mostrar_aviso_menor'] = True
            contexto['error'] = (
                'Para registrar una cuenta siendo menor de 18 años, confirma que '
                'tienes autorización y supervisión de una persona adulta responsable.'
            )
            return render(request, 'registrarse.html', contexto)

        enfoque = request.POST.get('enfoque_corporal', 'full_body')
        if enfoque not in ('inferior', 'superior', 'full_body'):
            contexto['error'] = 'Selecciona un enfoque corporal válido.'
            return render(request, 'registrarse.html', contexto)
        documento = request.POST.get('documento', '').strip()
        tipo_documento = request.POST.get('tipo_documento', '').strip().upper()
        tipos_documento_validos = {valor for valor, _ in TipoDocumentoChoice.choices}
        if bool(documento) != bool(tipo_documento):
            contexto['error'] = 'Para guardar un documento, completa tanto el tipo como el número; ambos campos también pueden dejarse vacíos.'
            return render(request, 'registrarse.html', contexto)
        if tipo_documento and tipo_documento not in tipos_documento_validos:
            contexto['error'] = 'Selecciona un tipo de documento válido.'
            return render(request, 'registrarse.html', contexto)
        elegido = request.session.get('plan_precio_pendiente', '')
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=email, email=email, password=password,
                    first_name=nombre, last_name=apellido,
                )
                perfil = get_perfil(user)
                if elegido in ('mensual', 'semestral', 'premium_anual'):
                    perfil.plan_precio = elegido
                perfil.enfoque_corporal = enfoque
                perfil.priorizar_tren_inferior = enfoque == 'inferior'
                perfil.fecha_nacimiento = fecha_nacimiento
                perfil.edad = calcular_edad(fecha_nacimiento)
                perfil.documento = documento
                perfil.tipo_documento = tipo_documento
                perfil.telefono = request.POST.get('telefono', '').strip() or None
                perfil.direccion = request.POST.get('direccion', '').strip() or None
                perfil.save(update_fields=[
                    'fecha_nacimiento', 'documento', 'tipo_documento',
                    'plan_precio', 'enfoque_corporal', 'priorizar_tren_inferior',
                    'edad', 'telefono', 'direccion',
                ])
        except IntegrityError:
            contexto['error'] = 'No se pudo completar el registro. Revisa el correo e inténtalo nuevamente.'
            return render(request, 'registrarse.html', contexto)
        request.session.pop('plan_precio_pendiente', None)
        login(request, user)
        return redirect('revisar_registro')

    return render(request, 'registrarse.html', {'enfoque_actual': 'full_body'})

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
@proteger_sesion_en_curso
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
@proteger_sesion_en_curso
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
@proteger_sesion_en_curso
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
@proteger_sesion_en_curso
def configurar_rutina_view(request):
    perfil = get_perfil(request.user)
    paso = siguiente_paso_personalizacion(perfil)
    if paso in ('objetivo', 'nivel_entrenamiento', 'prueba_nivel'):
        return redirect(paso)

    contexto = {
        'perfil': perfil,
        'enfoque_actual': perfil.enfoque_corporal,
        'dias_semana': DiaSemanaChoice.choices,
        'modalidades': ModalidadRutinaChoice.choices,
        'descanso_valor': max(1, round(perfil.descanso_preferido_segundos / 60)) if perfil.descanso_preferido_segundos % 60 == 0 else perfil.descanso_preferido_segundos,
        'descanso_unidad': 'minutos' if perfil.descanso_preferido_segundos % 60 == 0 else 'segundos',
    }
    if request.method == 'POST':
        dias = _normalizar_dias(request.POST.getlist('dias'))
        modalidad = request.POST.get('modalidad')
        try:
            minutos = int(request.POST.get('minutos', ''))
            if 'descanso_valor' in request.POST:
                descanso_valor = int(request.POST.get('descanso_valor', ''))
                descanso_unidad = request.POST.get('descanso_unidad', '')
                if descanso_unidad not in ('segundos', 'minutos'):
                    raise ValueError
                descanso = descanso_valor * (60 if descanso_unidad == 'minutos' else 1)
                contexto['descanso_valor'] = descanso_valor
                contexto['descanso_unidad'] = descanso_unidad
            else:
                # Compatibilidad con formularios abiertos antes del cambio.
                descanso = int(request.POST.get('descanso', ''))
                contexto['descanso_valor'] = descanso
                contexto['descanso_unidad'] = 'segundos'
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
                'priorizar_tren_inferior', 'enfoque_corporal',
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
        contexto['dias_formulario_enviado'] = True
        contexto['dias_seleccionados'] = [int(dia) for dia in dias]
        contexto['enfoque_actual'] = request.POST.get('enfoque_corporal', perfil.enfoque_corporal)

    return render(request, 'configurar_rutina.html', contexto)


@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
@proteger_sesion_en_curso
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
            if horario.numero_dia_plan > len(perfil.dias_entrenamiento):
                continue
            # Conservar los ejercicios por sesión aunque cambien los días elegidos.
            numero = horario.numero_dia_plan
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

    def render_datos_personales(error=None, status=200):
        form_data = request.POST if request.method == 'POST' else None
        if form_data is not None:
            metodo_seleccionado = form_data.get('metodo_grasa', 'omitir')
        elif perfil.metodo_estimacion_grasa == MetodoGrasaChoice.VISUAL and perfil.porcentaje_grasa_estimado is not None:
            metodo_seleccionado = f'visual:{int(perfil.porcentaje_grasa_estimado)}'
        elif perfil.metodo_estimacion_grasa == MetodoGrasaChoice.NAVY:
            metodo_seleccionado = 'navy'
        else:
            metodo_seleccionado = 'omitir'

        opciones_visuales = {
            genero: [
                {
                    'valor': valor,
                    'posicion': f'{indice * 100 / 6:.4f}%',
                    'seleccion': f'visual:{valor}',
                }
                for indice, valor in enumerate(valores)
            ]
            for genero, valores in REFERENCIAS_GRASA_VISUAL.items()
        }
        return render(request, 'datos_personales.html', {
            'perfil': perfil,
            'error': error,
            'form_data': form_data,
            'metodo_grasa_seleccionado': metodo_seleccionado,
            'opciones_visuales': opciones_visuales,
        }, status=status)

    if request.method == 'POST':
        perfil.genero = (
            request.POST.get('genero')
            or perfil.genero
            or None
        )
        if perfil.genero not in GeneroChoice.values:
            return render_datos_personales('Selecciona un género válido para continuar.', 400)
        peso_registro = request.POST.get('peso') or None
        from .profile_validation import validar_medida
        try:
            perfil.altura_cm = validar_medida(request.POST.get('altura_cm') or perfil.altura_cm, 'altura_cm')
            perfil.peso = validar_medida(peso_registro or perfil.peso, 'peso')
        except ValidationError as error:
            return render_datos_personales(error.messages[0], 400)
        if peso_registro and perfil.peso_inicial is None:
            perfil.peso_inicial = perfil.peso

        fecha_nacimiento = request.POST.get('fecha_nacimiento') or None
        if fecha_nacimiento:
            try:
                perfil.fecha_nacimiento = validar_fecha_nacimiento(fecha_nacimiento)
                perfil.edad = calcular_edad(perfil.fecha_nacimiento)
            except ValidationError as error:
                return render_datos_personales(error.messages[0], 400)
        elif perfil.fecha_nacimiento is not None:
            try:
                validar_fecha_nacimiento(perfil.fecha_nacimiento)
            except ValidationError as error:
                return render_datos_personales(error.messages[0], 400)
            perfil.edad = calcular_edad(perfil.fecha_nacimiento)

        if request.FILES.get('foto'):
            from .profile_validation import normalizar_foto
            try:
                perfil.foto = normalizar_foto(request.FILES['foto'])
            except ValidationError as error:
                return render_datos_personales(error.messages[0], 400)

        if not perfil.genero or not perfil.peso or perfil.fecha_nacimiento is None:
            return render_datos_personales('Completa género, peso y fecha de nacimiento para continuar.', 400)

        metodo_grasa = request.POST.get('metodo_grasa', 'omitir')
        edad_actual = calcular_edad(perfil.fecha_nacimiento)
        perfil.porcentaje_grasa_estimado = None
        perfil.metodo_estimacion_grasa = ''
        if edad_actual >= 20:
            try:
                if metodo_grasa.startswith('visual:'):
                    valor = int(metodo_grasa.partition(':')[2])
                    if valor not in REFERENCIAS_GRASA_VISUAL.get(perfil.genero, ()):
                        raise ValidationError('Selecciona una referencia visual que corresponda a la opción de género elegida.')
                    perfil.porcentaje_grasa_estimado = valor
                    perfil.metodo_estimacion_grasa = MetodoGrasaChoice.VISUAL
                elif metodo_grasa == 'navy':
                    porcentaje = estimar_grasa_navy(
                        perfil.genero,
                        perfil.altura_cm,
                        request.POST.get('medida_abdomen'),
                        request.POST.get('medida_cuello'),
                        request.POST.get('medida_cadera') or None,
                    )
                    perfil.porcentaje_grasa_estimado = porcentaje
                    perfil.metodo_estimacion_grasa = MetodoGrasaChoice.NAVY
                elif metodo_grasa != 'omitir':
                    raise ValidationError('Selecciona una imagen, las medidas con cinta o continuar sin estimar.')
            except (ValidationError, TypeError, ValueError) as error:
                mensaje = error.messages[0] if isinstance(error, ValidationError) else 'Revisa la selección de composición corporal.'
                return render_datos_personales(mensaje, 400)
        elif metodo_grasa != 'omitir':
            return render_datos_personales(
                'La estimación de composición corporal está disponible en este formulario solo para personas de 20 años o más.',
                400,
            )

        perfil.datos_completos = True
        perfil.save()
        evaluacion = perfil.evaluacion_corporal_interna()
        return redirect('resultado_corporal')

    return render_datos_personales()


@login_required(login_url='login')
def resultado_corporal_view(request):
    perfil = get_perfil(request.user)
    if not perfil.datos_completos:
        return redirect('datos_personales')
    return render(request, 'resultado_corporal.html', {
        'perfil': perfil,
        'evaluacion': perfil.evaluacion_corporal_interna(),
    })

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
                messages.error(request, 'La contraseña no coincide. No se eliminó tu cuenta.')
                return redirect('cuenta')
            user = request.user
            from django.db.models.deletion import ProtectedError
            from .models import (
                AsignacionPlanUsuario,
                GrupoAmigos,
                ParticipacionGrupal,
                PlanEntrenamiento,
                RecompensaEjercicio,
            )
            try:
                with transaction.atomic():
                    sesiones_usuario = SesionEntrenamiento.objects.filter(
                        asignacion__usuario=user
                    ).values_list('pk', flat=True)
                    # Preserve a shared group by transferring its administration
                    # before deleting the owner. A group with no other members can
                    # be removed along with its now-private proposals/results.
                    grupos_administrados = GrupoAmigos.objects.select_for_update().filter(
                        administrador=user
                    )
                    for grupo in grupos_administrados:
                        sucesor = grupo.integrantes.exclude(usuario=user).select_related(
                            'usuario'
                        ).order_by('desde').first()
                        if sucesor:
                            grupo.administrador = sucesor.usuario
                            grupo.save(update_fields=['administrador'])
                        else:
                            # Group participations point to sessions with PROTECT;
                            # detach those links so deleting an empty group cannot
                            # block removal of the account that owns the sessions.
                            ParticipacionGrupal.objects.filter(
                                rutina__grupo=grupo
                            ).update(sesion=None)
                            grupo.delete()

                    # These records belong to the account being erased. Remove the
                    # protective references first; shared group summaries and the
                    # other members' workouts remain untouched.
                    RecompensaEjercicio.objects.filter(usuario=user).delete()
                    ParticipacionGrupal.objects.filter(
                        Q(usuario=user) | Q(sesion_id__in=sesiones_usuario)
                    ).update(sesion=None)
                    # Remove this account's assignment/history before its private
                    # custom plans cascade. If another account still uses one of
                    # those plans, keep it but detach the deleted owner.
                    planes_propios = PlanEntrenamiento.objects.filter(propietario=user)
                    AsignacionPlanUsuario.objects.filter(usuario=user).delete()
                    # Materialize IDs first: MySQL rejects updating a table while
                    # selecting from that same table in an UPDATE subquery (1093).
                    planes_compartidos = list(
                        AsignacionPlanUsuario.objects.filter(
                            plan__in=planes_propios
                        ).values_list('plan_id', flat=True).distinct()
                    )
                    planes_propios.filter(pk__in=planes_compartidos).update(propietario=None)
                    user.delete()
            except ProtectedError:
                logger.exception(
                    'Eliminación detenida por una relación protegida user_id=%s',
                    user.pk,
                )
                messages.error(
                    request,
                    'No se pudo eliminar la cuenta porque todavía está vinculada a '
                    'información compartida. No se borró ningún dato; contacta al '
                    'soporte para revisarlo.',
                )
                return redirect('cuenta')
            except Exception:
                # Railway's access log only reports the HTTP 500; explicitly log
                # the traceback so the next failure identifies the DB/model cause.
                logger.exception(
                    'Fallo inesperado al eliminar la cuenta user_id=%s', user.pk
                )
                messages.error(
                    request,
                    'No se pudo completar la eliminación por un error interno. '
                    'No se borró ningún dato; inténtalo más tarde o contacta al soporte.',
                )
                return redirect('cuenta')
            logout(request)
            return redirect('inicio')

        if accion in ['actualizar_cuenta', 'actualizar_foto']:
            from .profile_validation import normalizar_foto, validar_medida
            try:
                if request.FILES.get('foto'):
                    perfil.foto = normalizar_foto(request.FILES['foto'])
                if accion == 'actualizar_cuenta':
                    for campo in ('peso', 'peso_inicial', 'altura_cm'):
                        if request.POST.get(campo):
                            setattr(perfil, campo, validar_medida(request.POST[campo], campo))
            except ValidationError as error:
                return JsonResponse({'ok': False, 'error': error.messages[0]}, status=400)

            if accion == 'actualizar_cuenta':
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
                perfil.peso_inicial = perfil.peso_inicial or perfil.peso

            with transaction.atomic():
                if accion == 'actualizar_cuenta':
                    request.user.save()
                perfil.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'ok': True, 'foto_url': perfil.foto.url if perfil.foto else ''})
            return redirect('cuenta')

        logger.warning(
            'POST de cuenta con acción no reconocida user_id=%s accion=%r',
            request.user.pk,
            accion,
        )
        messages.error(
            request,
            'No se recibió una acción válida. Recarga la página e inténtalo de nuevo.',
        )
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

    # Una rutina creada por el usuario nunca debe ser reemplazada visualmente
    # por una propuesta automática antigua.  Normalmente sólo existe una
    # asignación activa, pero este orden también protege los datos de cuentas
    # que fueron configuradas antes de que existiera la rutina personalizada.
    asignaciones_activas = (
        request.user.planes_asignados
        .filter(estado=EstadoAsignacionChoice.ACTIVO)
        .select_related("plan")
        .prefetch_related("horarios")
    )
    if perfil.modalidad_rutina == ModalidadRutinaChoice.PERSONALIZADA:
        asignacion = asignaciones_activas.annotate(
            es_rutina_manual=Case(
                When(
                    plan__nombre__startswith="Rutina creada por el usuario",
                    then=Value(1),
                ),
                default=Value(0),
                output_field=IntegerField(),
            )
        ).order_by(
            "-es_rutina_manual",
            "-fecha_creacion",
            "-pk",
        ).first()
    else:
        asignacion = asignaciones_activas.order_by(
            "-fecha_creacion",
            "-pk",
        ).first()

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
        "ciclo_rutina": None,
        "siguiente_sesion": None,
    }

    if asignacion is None:
        return render(
            request,
            "mi_entrenamiento.html",
            context,
        )

    fase_actual = asignacion.fase_actual
    hoy = timezone.localdate()

    # Estado imposible que pudo quedar por una versión anterior: una sesión
    # futura no se ha podido iniciar todavía. Se devuelve a pendiente para que
    # no bloquee la edición ni aparezca activa antes de su día.
    asignacion.sesiones.filter(
        estado=EstadoSesionChoice.EN_PROGRESO,
        fecha__gt=hoy,
    ).update(
        estado=EstadoSesionChoice.PENDIENTE,
        fecha_inicio=None,
        fecha_actualizacion=timezone.now(),
    )

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

    lunes = hoy - timedelta(days=hoy.weekday())
    domingo = lunes + timedelta(days=6)
    sesiones_semana = {
        sesion.dia_plan_id: sesion
        for sesion in asignacion.sesiones.filter(
            fecha__lte=hoy,
        ).filter(Q(fecha_programada__range=(lunes, domingo)) |
                 Q(fecha_programada__isnull=True, fecha__range=(lunes, domingo)))
    }

    calendario_semana = []
    for horario in horarios:
        dia_plan = dias_fase.get(horario.numero_dia_plan)
        sesion = sesiones_semana.get(dia_plan.id) if dia_plan else None
        fecha_prevista = lunes + timedelta(days=horario.dia_semana)
        calendario_semana.append({
            "horario": horario,
            "dia_plan": dia_plan,
            "sesion": sesion,
            "fecha_prevista": fecha_prevista,
            "puede_reponer": bool(dia_plan and asignacion.fecha_inicio <= fecha_prevista < hoy
                                  and not (sesion and sesion.estado == EstadoSesionChoice.COMPLETADA)),
            "es_completada": bool(
                sesion and sesion.estado == EstadoSesionChoice.COMPLETADA
            ),
            "es_en_curso": bool(
                sesion
                and sesion.estado == EstadoSesionChoice.EN_PROGRESO
                and sesion.fecha == hoy
            ),
        })

    siguiente_sesion = next(
        (
            elemento for elemento in calendario_semana
            if not elemento["es_completada"]
        ),
        None,
    )

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

        if accion == 'reponer_dia':
            elemento = next((e for e in calendario_semana
                             if e['puede_reponer'] and str(e['dia_plan'].pk) == request.POST.get('dia_plan_id')), None)
            if elemento is None:
                messages.error(request, 'Selecciona uno de tus días pendientes de esta semana.')
            else:
                try:
                    sesion, _ = iniciar_sesion_entrenamiento(
                        asignacion, elemento['dia_plan'], fecha_programada=elemento['fecha_prevista'],
                    )
                except ValidationError as error:
                    messages.error(request, ' '.join(error.messages))
                else:
                    messages.success(request, 'Vamos a retomar ese día. Al completar la sesión contará para tu semana.')
                    return redirect('reproductor_entrenamiento', sesion_id=sesion.pk)
        elif accion == "iniciar_sesion":
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
                fecha=hoy,
                dia_plan=dia_hoy,
            )
            .filter(Q(fecha_programada=hoy) | Q(fecha_programada__isnull=True))
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

    from .training_streak import obtener_racha
    racha = obtener_racha(asignacion, hoy, horarios)
    context.update({
        "fase_actual": fase_actual,
        "semana_actual": asignacion.semana_actual,
        "calendario_semana": calendario_semana,
        "horario_hoy": horario_hoy,
        "dia_hoy": dia_hoy,
        "ejercicios_hoy": ejercicios_hoy,
        "sesion_hoy": sesion_hoy,
        "ciclo_rutina": racha,
        "sesion_elegida_hoy": SesionEntrenamiento.objects.filter(
            asignacion__usuario=request.user, fecha=hoy).select_related('dia_plan').first(),
        "siguiente_sesion": siguiente_sesion,
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
