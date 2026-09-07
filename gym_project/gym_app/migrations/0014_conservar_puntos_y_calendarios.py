from datetime import timedelta
from django.db import migrations


def conservar(apps, schema_editor):
    Registro = apps.get_model('gym_app', 'EjercicioSesion')
    Recompensa = apps.get_model('gym_app', 'RecompensaEjercicio')
    Asignacion = apps.get_model('gym_app', 'AsignacionPlanUsuario')
    Compromiso = apps.get_model('gym_app', 'DiaComprometido')
    alias = schema_editor.connection.alias
    # No recalcular ni borrar los puntos históricos, incluso si había duplicados.
    for r in Registro.objects.using(alias).filter(completado=True).select_related('sesion__asignacion', 'ejercicio_programado').order_by('pk').iterator():
        Recompensa.objects.using(alias).get_or_create(usuario_id=r.sesion.asignacion.usuario_id,
            ejercicio_id=r.ejercicio_programado.ejercicio_id, fecha=r.sesion.fecha,
            defaults={'registro_id': r.pk, 'puntos': r.puntos_obtenidos})
    for a in Asignacion.objects.using(alias).select_related('plan').order_by('fecha_inicio', 'pk').iterator():
        final = a.fecha_inicio + timedelta(days=a.plan.duracion_semanas * 7 - 1)
        if a.fecha_fin:
            final = min(final, a.fecha_fin)
        siguiente = Asignacion.objects.using(alias).filter(usuario_id=a.usuario_id, fecha_inicio__gt=a.fecha_inicio).order_by('fecha_inicio').first()
        if siguiente:
            final = min(final, siguiente.fecha_inicio - timedelta(days=1))
        dias = set(a.horarios.filter(activo=True).values_list('dia_semana', flat=True))
        fecha = a.fecha_inicio
        while fecha <= final:
            if fecha.weekday() in dias:
                Compromiso.objects.using(alias).get_or_create(usuario_id=a.usuario_id, fecha=fecha)
            fecha += timedelta(days=1)


class Migration(migrations.Migration):
    dependencies = [('gym_app', '0013_grupoamigos_perfilusuario_priorizar_tren_inferior_and_more')]
    operations = [migrations.RunPython(conservar, migrations.RunPython.noop)]
