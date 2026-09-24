"""Progreso ganado con sesiones completas, independiente de la edad del plan."""
from datetime import timedelta


def calcular_racha(fechas_completadas, fechas_programadas, hoy, dias_por_semana):
    completadas = sorted({f for f in fechas_completadas if f <= hoy})
    resultado = dict(estado='sin_iniciar', dias=0, semana=0, dia=0,
                     total_dias=dias_por_semana, semana_completada=False)
    if not completadas or not dias_por_semana:
        return resultado
    # Solo exigimos los días elegidos; hasta el domingo se pueden reponer.
    semanas = {}
    for fecha in fechas_programadas:
        if fecha >= completadas[0]:
            lunes = fecha - timedelta(days=fecha.weekday())
            semanas.setdefault(lunes, set()).add(fecha)
    incumplidas = [lunes + timedelta(days=6) for lunes, dias in semanas.items()
                   if lunes + timedelta(days=6) < hoy and not dias.issubset(set(completadas))]
    ultimo_cierre = max(incumplidas) if incumplidas else None
    consecutivas = [f for f in completadas if not ultimo_cierre or f > ultimo_cierre]
    if not consecutivas:
        resultado['estado'] = 'reiniciada'
        return resultado
    cantidad = len(consecutivas)
    resultado.update(estado='activa', dias=cantidad,
                     semana=(cantidad - 1) // dias_por_semana + 1,
                     dia=(cantidad - 1) % dias_por_semana + 1,
                     semana_completada=cantidad % dias_por_semana == 0)
    faltas_abiertas = any(
        lunes <= hoy <= lunes + timedelta(days=6)
        and any(f < hoy and f not in completadas for f in dias)
        for lunes, dias in semanas.items()
    )
    if faltas_abiertas:
        resultado['estado'] = 'pendiente'
    return resultado


def obtener_racha(asignacion, hoy, horarios):
    from .models import DiaComprometido, SesionEntrenamiento
    fechas = [programada or realizada for realizada, programada in SesionEntrenamiento.objects.filter(
        asignacion__usuario_id=asignacion.usuario_id,
        estado='completada', fecha__lte=hoy,
    ).values_list('fecha', 'fecha_programada')]
    if not fechas:
        return calcular_racha([], [], hoy, len(horarios))
    fin_semana = hoy + timedelta(days=6-hoy.weekday())
    compromisos = dict(DiaComprometido.objects.filter(
        usuario_id=asignacion.usuario_id, fecha__gte=min(fechas), fecha__lte=fin_semana,
    ).values_list('fecha', 'cancelado'))
    programadas = {f for f, cancelado in compromisos.items() if not cancelado}
    # Completar el calendario actual si terminó la ventana precargada de 16 semanas.
    dias = {h.dia_semana for h in horarios}
    fecha = max(min(fechas), asignacion.fecha_inicio)
    while fecha <= fin_semana:
        if fecha not in compromisos and fecha.weekday() in dias:
            programadas.add(fecha)
        fecha += timedelta(days=1)
    return calcular_racha(fechas, programadas, hoy, len(horarios))
