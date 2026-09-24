from django.db import migrations, models


def conservar_fecha(apps, schema_editor):
    apps.get_model('gym_app', 'SesionEntrenamiento').objects.using(
        schema_editor.connection.alias
    ).update(fecha_programada=models.F('fecha'))


class Migration(migrations.Migration):
    dependencies = [('gym_app', '0017_rutinas_personalizadas_continuas')]
    operations = [
        migrations.AddField(model_name='sesionentrenamiento', name='fecha_programada',
                            field=models.DateField(null=True, blank=True)),
        migrations.RunPython(conservar_fecha, migrations.RunPython.noop),
    ]
