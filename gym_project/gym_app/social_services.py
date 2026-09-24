from datetime import timedelta
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from .models import (PerfilUsuario, GrupoAmigos, IntegranteGrupo, RecompensaEjercicio,
    DiaComprometido, RutinaGrupal, ParticipacionGrupal, AvisoSocial, ResultadoGrupo,
    SesionEntrenamiento, AsignacionPlanUsuario, DiaPlan, EjercicioProgramado, EjercicioSesion)


def guardar_calendario(asignacion):
    hoy = timezone.localdate()
    # Nunca reescribir el pasado ni el compromiso de hoy.
    DiaComprometido.objects.filter(usuario=asignacion.usuario, fecha__gt=hoy).update(cancelado=True)
    dias = set(asignacion.horarios.filter(activo=True).values_list('dia_semana', flat=True))
    # El calendario social sólo necesita una ventana futura razonable. La
    # rutina como tal sigue repitiéndose sin caducar; evitar crear decenas de
    # miles de filas al configurar una rutina de larga duración.
    semanas_calendario = min(asignacion.plan.duracion_semanas, 16)
    for offset in range(semanas_calendario * 7):
        fecha = asignacion.fecha_inicio + timedelta(days=offset)
        if fecha >= hoy and fecha.weekday() in dias:
            compromiso, nuevo = DiaComprometido.objects.get_or_create(usuario=asignacion.usuario, fecha=fecha)
            if not nuevo and fecha > hoy and compromiso.cancelado:
                compromiso.cancelado = False
                compromiso.save(update_fields=['cancelado'])


def resumen_usuario(usuario, inicio=None, fin=None):
    hoy = timezone.localdate()
    fechas = set(SesionEntrenamiento.objects.filter(asignacion__usuario=usuario, estado='completada', fecha__lte=hoy).values_list('fecha', flat=True))
    acreditadas = {programada or realizada for realizada, programada in
        SesionEntrenamiento.objects.filter(asignacion__usuario=usuario, estado='completada', fecha__lte=hoy)
        .values_list('fecha', 'fecha_programada')}
    compromisos = list(DiaComprometido.objects.filter(usuario=usuario, cancelado=False, fecha__lte=hoy).order_by('fecha').values_list('fecha', flat=True))
    racha = mejor = 0
    semanas = {}
    for fecha in compromisos:
        if acreditadas and fecha >= min(acreditadas):
            semanas.setdefault(fecha - timedelta(days=fecha.weekday()), set()).add(fecha)
    for lunes, dias in sorted(semanas.items()):
        racha += len(dias & acreditadas)
        mejor = max(mejor, racha)
        if lunes + timedelta(days=6) < hoy and not dias.issubset(acreditadas):
            racha = 0
    inicio = inicio or hoy - timedelta(days=hoy.weekday())
    fin = fin or inicio + timedelta(days=6)
    programados = [f for f in compromisos if inicio <= f <= min(fin, hoy)]
    cumplidos = sum(f in acreditadas for f in programados)
    sesiones = SesionEntrenamiento.objects.filter(asignacion__usuario=usuario)
    return {'id': usuario.pk, 'nombre': usuario.get_full_name() or usuario.username.split('@')[0],
            'racha': racha, 'mejor': mejor,
            'puntos': sesiones.aggregate(total=Sum('puntos_obtenidos'))['total'] or 0,
            'semanales': sesiones.filter(fecha__range=(inicio, fin)).aggregate(total=Sum('puntos_obtenidos'))['total'] or 0,
            'dias': min(6, sum(inicio <= f <= fin for f in fechas)),
            'cumplidos': cumplidos, 'programados': len(programados),
            'constancia': round(100 * cumplidos / len(programados)) if programados else 0}


@transaction.atomic
def unirse(usuario, codigo):
    PerfilUsuario.objects.select_for_update().get(user=usuario)
    if IntegranteGrupo.objects.filter(usuario=usuario).exists():
        raise ValidationError('Ya perteneces a un grupo. Sal de él antes de unirte a otro.')
    grupo = GrupoAmigos.objects.select_for_update().get(invitacion=codigo)
    if grupo.integrantes.count() >= 7:
        raise ValidationError('Este grupo ya tiene siete integrantes.')
    IntegranteGrupo.objects.create(usuario=usuario, grupo=grupo)
    AvisoSocial.objects.create(usuario=grupo.administrador, texto=f'{usuario.first_name or "Un amigo"} se unió a {grupo.nombre}.')
    return grupo


@transaction.atomic
def comenzar_grupal(usuario, rutina):
    from .services import _crear_plan_vacio, _valores_programacion, asegurar_series_sesion, _segundos_estimados
    perfil = PerfilUsuario.objects.select_for_update().get(user=usuario)
    rutina = RutinaGrupal.objects.select_for_update().get(pk=rutina.pk)
    if not IntegranteGrupo.objects.filter(usuario=usuario, grupo=rutina.grupo).exists():
        raise ValidationError('Ya no perteneces a este grupo.')
    participacion = ParticipacionGrupal.objects.select_for_update().get(usuario=usuario, rutina=rutina)
    if participacion.sesion_id:
        return participacion.sesion
    hoy = timezone.localdate()
    if rutina.fecha != hoy or participacion.revision != rutina.revision:
        raise ValidationError('Acepta la versión actual y comienza en el día acordado.')
    if SesionEntrenamiento.objects.filter(asignacion__usuario=usuario, fecha=hoy).exists():
        raise ValidationError('Ya tienes una sesión hoy. Continúala; no añadiremos otra encima.')
    if not DiaComprometido.objects.filter(usuario=usuario, fecha=hoy, cancelado=False).exists():
        raise ValidationError('Esta rutina debe sustituir un día de tu calendario personal.')
    ejercicios = list(rutina.ejercicios.filter(activo=True).order_by('pk'))
    if not ejercicios:
        raise ValidationError('La rutina no contiene ejercicios disponibles.')
    niveles = ['principiante', 'intermedio', 'encima_promedio', 'avanzado']
    if perfil.nivel_entrenamiento not in niveles or any(niveles.index(e.nivel) > niveles.index(perfil.nivel_entrenamiento) for e in ejercicios):
        raise ValidationError('Hay ejercicios por encima de tu nivel. Pide al administrador una propuesta compatible.')
    programaciones = [(e, _valores_programacion(e, perfil.nivel_entrenamiento, perfil.descanso_preferido_segundos)) for e in ejercicios]
    disponibles = perfil.minutos_por_dia.get(str(hoy.weekday()), perfil.duracion_sesion_minutos)
    if 600 + sum(_segundos_estimados(v) for _, v in programaciones) > disponibles * 60:
        raise ValidationError('La propuesta supera tu tiempo disponible con tus descansos. Pide una sesión más corta o ajusta tu disponibilidad.')
    plan, fase = _crear_plan_vacio(usuario, perfil.objetivo, perfil.nivel_entrenamiento, 1, rutina.titulo)
    dia = DiaPlan.objects.create(fase=fase, numero=1, nombre=rutina.titulo)
    # Archivo independiente: no sustituir la asignación personal ni alterar sus ejercicios.
    asignacion = AsignacionPlanUsuario.objects.create(usuario=usuario, plan=plan, fecha_inicio=hoy, estado='abandonado', fecha_fin=hoy)
    sesion = SesionEntrenamiento.objects.create(asignacion=asignacion, dia_plan=dia, fecha=hoy, semana_plan=1, estado='en_progreso', fecha_inicio=timezone.now())
    for orden, (ejercicio, valores) in enumerate(programaciones, 1):
        p = EjercicioProgramado.objects.create(dia=dia, ejercicio=ejercicio, orden=orden,
            **valores)
        EjercicioSesion.objects.create(sesion=sesion, ejercicio_programado=p)
    asegurar_series_sesion(sesion)
    participacion.sesion = sesion
    participacion.save(update_fields=['sesion'])
    return sesion


def clasificacion(grupo, inicio=None):
    filas = [resumen_usuario(m.usuario, inicio) for m in grupo.integrantes.select_related('usuario')]
    return sorted(filas, key=lambda f: (-f['constancia'], -f['semanales'], f['id']))


def registrar_meta(usuario):
    miembro = IntegranteGrupo.objects.filter(usuario=usuario).first()
    if not miembro:
        return
    hoy = timezone.localdate()
    lunes = hoy - timedelta(days=hoy.weekday())
    grupo = GrupoAmigos.objects.select_for_update().get(pk=miembro.grupo_id)
    filas = clasificacion(grupo)
    if not filas or not all(f['cumplidos'] >= 2 for f in filas):
        return
    resultado, _ = ResultadoGrupo.objects.get_or_create(grupo=grupo, semana=lunes)
    if not resultado.insignia:
        resultado.insignia = True
        resultado.save(update_fields=['insignia'])
        AvisoSocial.objects.bulk_create([AvisoSocial(usuario=m.usuario, texto=f'¡{grupo.nombre} alcanzó la meta colectiva semanal! Insignia de constancia desbloqueada.') for m in grupo.integrantes.select_related('usuario')])


def archivar_semana(grupo):
    hoy = timezone.localdate()
    lunes = hoy - timedelta(days=hoy.weekday())
    semana = lunes - timedelta(days=7)
    if grupo.creado.date() > semana + timedelta(days=6):
        return
    filas = clasificacion(grupo, semana)
    resultado, creado = ResultadoGrupo.objects.get_or_create(grupo=grupo, semana=semana,
        defaults={'clasificacion': filas, 'insignia': bool(filas) and all(f['cumplidos'] >= 2 for f in filas)})
    if not creado and not resultado.clasificacion:
        resultado.clasificacion = filas
        resultado.save(update_fields=['clasificacion'])
