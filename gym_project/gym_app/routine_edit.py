from functools import wraps
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import SesionEntrenamiento, EstadoSesionChoice, PerfilUsuario


def entrenamiento_en_curso(user):
    return SesionEntrenamiento.objects.filter(asignacion__usuario=user, estado=EstadoSesionChoice.EN_PROGRESO).exists()


def proteger_sesion_en_curso(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if request.user.is_authenticated and entrenamiento_en_curso(request.user):
            messages.info(request, 'Finaliza tu sesión actual antes de modificar la rutina. Tus avances se conservan.')
            return redirect('modificar_rutina')
        return view(request, *args, **kwargs)
    return wrapped


@login_required
def modificar_rutina(request):
    return render(request, 'modificar_rutina.html', {
        'en_curso': entrenamiento_en_curso(request.user),
        'perfil': PerfilUsuario.objects.get(user=request.user),
    })
