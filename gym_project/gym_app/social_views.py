import uuid
from datetime import date, time
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from .models import (PerfilUsuario, GrupoAmigos, IntegranteGrupo, RutinaGrupal,
    ParticipacionGrupal, AvisoSocial, DiaComprometido, Ejercicio)
from .social_services import unirse, comenzar_grupal, resumen_usuario, clasificacion, archivar_semana


@login_required
@require_http_methods(['GET', 'POST'])
def amigos(request):
    miembro = IntegranteGrupo.objects.select_related('grupo').filter(usuario=request.user).first()
    if request.method == 'POST':
        try:
            with transaction.atomic():
                PerfilUsuario.objects.select_for_update().get(user=request.user)
                accion = request.POST.get('accion')
                if accion == 'crear':
                    if IntegranteGrupo.objects.filter(usuario=request.user).exists():
                        raise ValidationError('Ya tienes un grupo activo.')
                    nombre = request.POST.get('nombre', '').strip()
                    if not nombre or len(nombre) > 80:
                        raise ValidationError('Escribe un nombre de hasta 80 caracteres.')
                    grupo = GrupoAmigos(nombre=nombre, administrador=request.user)
                    if request.FILES.get('imagen'):
                        from PIL import Image
                        archivo = request.FILES['imagen']
                        if archivo.size > 3 * 1024 * 1024:
                            raise ValidationError('La imagen debe pesar menos de 3 MB.')
                        try:
                            Image.open(archivo).verify()
                            archivo.seek(0)
                        except Exception:
                            raise ValidationError('Selecciona una imagen válida.')
                        grupo.imagen = archivo
                    grupo.save()
                    IntegranteGrupo.objects.create(usuario=request.user, grupo=grupo)
                elif accion == 'unirse':
                    unirse(request.user, uuid.UUID(request.POST.get('codigo', '').strip()))
                elif miembro:
                    grupo = GrupoAmigos.objects.select_for_update().get(pk=miembro.grupo_id)
                    if accion == 'salir':
                        if grupo.administrador_id == request.user.pk:
                            sucesor = grupo.integrantes.exclude(usuario=request.user).order_by('desde').first()
                            if sucesor:
                                grupo.administrador = sucesor.usuario
                                grupo.save(update_fields=['administrador'])
                            else:
                                grupo.delete()
                                return redirect('amigos')
                        miembro.delete()
                    elif accion in ('retirar', 'renovar'):
                        if grupo.administrador_id != request.user.pk:
                            raise ValidationError('Solo el administrador puede gestionar integrantes.')
                        if accion == 'renovar':
                            grupo.invitacion = uuid.uuid4()
                            grupo.save(update_fields=['invitacion'])
                        else:
                            grupo.integrantes.exclude(usuario=request.user).filter(usuario_id=request.POST.get('usuario')).delete()
                    else:
                        raise ValidationError('Acción no válida.')
                else:
                    raise ValidationError('Primero crea un grupo o únete a uno.')
        except (ValidationError, ValueError, GrupoAmigos.DoesNotExist) as error:
            messages.error(request, ' '.join(error.messages) if isinstance(error, ValidationError) else 'El código de invitación no es válido.')
        return redirect('amigos')
    grupo = miembro.grupo if miembro else None
    if grupo:
        archivar_semana(grupo)
    filas = clasificacion(grupo) if grupo else []
    return render(request, 'amigos.html', {'grupo': grupo, 'perfil': PerfilUsuario.objects.get(user=request.user),
        'resumen': resumen_usuario(request.user), 'clasificacion': filas,
        'actividad': sorted(filas, key=lambda f: (-f['dias'], -f['semanales'])),
        'invitacion_url': request.build_absolute_uri(reverse('amigos') + '?codigo=' + str(grupo.invitacion)) if grupo else '',
        'codigo': request.GET.get('codigo', ''),
        'resultados': grupo.resultadogrupo_set.exclude(clasificacion=[]).order_by('-semana')[:12] if grupo else [],
        'meta_cumplida': bool(filas) and all(f['cumplidos'] >= 2 for f in filas)})


@login_required
@require_http_methods(['GET', 'POST'])
def rutina_grupal(request, pk=None):
    miembro = get_object_or_404(IntegranteGrupo, usuario=request.user)
    grupo = miembro.grupo
    rutina = get_object_or_404(RutinaGrupal, pk=pk, grupo=grupo) if pk else None
    if request.method == 'POST':
        try:
            with transaction.atomic():
                PerfilUsuario.objects.select_for_update().get(user=request.user)
                grupo = GrupoAmigos.objects.select_for_update().get(pk=grupo.pk)
                if rutina:
                    rutina = RutinaGrupal.objects.select_for_update().get(pk=rutina.pk)
                accion = request.POST.get('accion')
                if accion == 'guardar':
                    if grupo.administrador_id != request.user.pk:
                        raise ValidationError('Solo el administrador propone o edita rutinas.')
                    fecha = date.fromisoformat(request.POST.get('fecha', ''))
                    if fecha < timezone.localdate() or (rutina and (rutina.fecha <= timezone.localdate() or rutina.participaciones.filter(sesion__isnull=False).exists())):
                        raise ValidationError('Solo puedes editar propuestas futuras que nadie haya comenzado.')
                    titulo = request.POST.get('titulo', '').strip()
                    ids = list(set(request.POST.getlist('ejercicios')))
                    ejercicios = list(Ejercicio.objects.filter(pk__in=ids, activo=True))
                    if not titulo or len(titulo) > 100 or not 1 <= len(ejercicios) <= 8 or len(ejercicios) != len(ids):
                        raise ValidationError('Escribe un título y selecciona de uno a ocho ejercicios.')
                    rutina = rutina or RutinaGrupal(grupo=grupo)
                    rutina.titulo, rutina.fecha = titulo, fecha
                    rutina.hora = time.fromisoformat(request.POST['hora']) if request.POST.get('hora') else None
                    rutina.revision += 1
                    rutina.save()
                    rutina.ejercicios.set(ejercicios)
                    AvisoSocial.objects.bulk_create([AvisoSocial(usuario=m.usuario, texto=f'Nueva propuesta: {titulo}. Revisa y acepta la rutina en Amigos.') for m in grupo.integrantes.select_related('usuario')])
                elif accion == 'aceptar' and rutina:
                    if rutina.fecha < timezone.localdate():
                        raise ValidationError('La fecha de esta sesión ya pasó.')
                    if not DiaComprometido.objects.filter(usuario=request.user, fecha=rutina.fecha, cancelado=False).exists():
                        raise ValidationError('Elige una propuesta que coincida con tu calendario; no se añadirá un día extra.')
                    ParticipacionGrupal.objects.update_or_create(usuario=request.user, rutina=rutina, defaults={'revision': rutina.revision})
                elif accion == 'comenzar' and rutina:
                    sesion = comenzar_grupal(request.user, rutina)
                    return redirect('reproductor_entrenamiento', sesion_id=sesion.pk)
                else:
                    raise ValidationError('Acción no válida.')
            return redirect('rutina_grupal', pk=rutina.pk)
        except (ValidationError, ValueError, ParticipacionGrupal.DoesNotExist) as error:
            messages.error(request, ' '.join(error.messages) if isinstance(error, ValidationError) else 'Revisa la fecha, los valores y la aceptación de la rutina.')
    return render(request, 'rutina_grupal.html', {'grupo': grupo, 'rutina': rutina,
        'ejercicios': Ejercicio.objects.filter(activo=True).order_by('grupo_muscular', 'nombre'),
        'seleccionados': list(rutina.ejercicios.values_list('pk', flat=True)) if rutina else [],
        'participacion': rutina.participaciones.filter(usuario=request.user).first() if rutina else None,
        'participaciones': rutina.participaciones.select_related('usuario', 'sesion') if rutina else [],
        'hoy': timezone.localdate()})
