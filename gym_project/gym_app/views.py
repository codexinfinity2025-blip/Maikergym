from datetime import date
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from gym_project.gym_app.models import (
    EstadoAsignacionChoice,
    PerfilUsuario,
    RolChoice,
)
from gym_project.gym_app.services import (
    asignar_plan_por_objetivo,
    iniciar_sesion_entrenamiento,
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
    'nutricion': {
        'titulo': 'Dieta nutricional personalizada',
        'descripcion': 'Plan inicial para ordenar horarios, grupos de alimentos y elecciones saludables según tus datos.',
    },
    'recuperar': {
        'titulo': 'Dieta para recuperación',
        'descripcion': 'Plan orientado a recuperación física, proteína suficiente, descanso y alimentos que apoyen el proceso.',
    },
}

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
    if not perfil.dieta_aceptada:
        return 'dieta'
    if not perfil.datos_completos:
        return 'datos_personales'
    return 'cuenta'

def inicio(request):
    return render(request, 'inicio.html')

def escogenos(request):
    return render(request, 'escogenos.html')

def precios(request):
    return render(request, 'precios.html')

@require_http_methods(["GET", "POST"])
def registrarse(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        apellido = request.POST.get('apellido', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        confirmar_password = request.POST.get('confirmar_password', '')

        if password != confirmar_password:
            return render(request, 'registrarse.html', {'error': 'Las contraseñas no coinciden.'})

        if User.objects.filter(email=email).exists():
            return render(request, 'registrarse.html', {'error': 'Ya existe una cuenta con ese correo.'})

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=nombre,
            last_name=apellido,
        )
        perfil = get_perfil(user)
        fecha_nacimiento = request.POST.get('fecha_nacimiento') or None
        if fecha_nacimiento:
            try:
                perfil.fecha_nacimiento = date.fromisoformat(fecha_nacimiento)
                perfil.edad = calcular_edad(perfil.fecha_nacimiento)
                perfil.save()
            except ValueError:
                pass
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
            perfil.objetivo = objetivo_elegido
            perfil.dieta_aceptada = False
            perfil.datos_completos = False
            perfil.save()
            asignar_plan_por_objetivo(
                request.user,
                objetivo_elegido,
)
            return redirect('dieta')
        return render(request, 'objetivo.html', {'error': 'Escoge un objetivo válido.'})
    return render(request, 'objetivo.html', {'perfil': perfil})

@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def dieta_view(request):
    perfil = get_perfil(request.user)
    if not perfil.objetivo:
        return redirect('objetivo')

    dieta = DIETAS_POR_OBJETIVO.get(perfil.objetivo, DIETAS_POR_OBJETIVO['salud'])
    if request.method == 'POST':
        if request.POST.get('acepta_dieta') == 'on':
            perfil.dieta_aceptada = True
            perfil.save()
            return redirect('datos_personales')
        return render(request, 'dieta.html', {'perfil': perfil, 'dieta': dieta, 'error': 'Debes aceptar la dieta para continuar.'})

    return render(request, 'dieta.html', {'perfil': perfil, 'dieta': dieta})

@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def datos_personales_view(request):
    perfil = get_perfil(request.user)
    if not perfil.objetivo:
        return redirect('objetivo')
    if not perfil.dieta_aceptada:
        return redirect('dieta')

    if request.method == 'POST':
        perfil.genero = request.POST.get('genero') or None
        peso_registro = request.POST.get('peso') or None
        perfil.peso = peso_registro
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
        return redirect('cuenta')

    return render(request, 'datos_personales.html', {'perfil': perfil})

def contacto(request):
    return render(request, 'contacto.html')

@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        rol = request.POST.get('rol', 'usuario')

        try:
            user = User.objects.get(email=email)
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
        except User.DoesNotExist:
            error = 'Correo o contraseña inválidos.'

        return render(request, 'login.html', {'error': error})

    return render(request, 'login.html')

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
            user = request.user
            logout(request)
            user.delete()
            return redirect('inicio')

        if accion in ['actualizar_cuenta', 'actualizar_foto']:
            if request.FILES.get('foto'):
                perfil.foto = request.FILES['foto']

            if accion == 'actualizar_cuenta':
                nombre_completo = request.POST.get('nombre', '').strip()
                if nombre_completo:
                    partes = nombre_completo.split()
                    request.user.first_name = partes[0]
                    request.user.last_name = ' '.join(partes[1:])

                email = request.POST.get('email', '').strip().lower()
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

        if accion != "iniciar_sesion":
            messages.error(
                request,
                "La acción solicitada no es válida.",
            )

        elif dia_hoy is None:
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

        return redirect("mi_entrenamiento")

    sesion_hoy = (
        asignacion.sesiones
        .filter(fecha=hoy)
        .prefetch_related(
            "ejercicios__ejercicio_programado__ejercicio"
        )
        .first()
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