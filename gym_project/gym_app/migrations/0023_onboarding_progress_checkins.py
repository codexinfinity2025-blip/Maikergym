# Generated for onboarding order and periodic progress check-ins.
import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def preserve_existing_onboarding(apps, schema_editor):
    PerfilUsuario = apps.get_model('gym_app', 'PerfilUsuario')
    for perfil in PerfilUsuario.objects.all().iterator():
        updates = []
        if perfil.datos_completos:
            perfil.composicion_corporal_completa = True
            updates.append('composicion_corporal_completa')
        if perfil.dias_entrenamiento or perfil.configuracion_entrenamiento_completa:
            perfil.disponibilidad_completa = True
            updates.append('disponibilidad_completa')
        if updates:
            perfil.save(update_fields=updates)


class Migration(migrations.Migration):

    dependencies = [
        ('gym_app', '0022_perfilusuario_metodo_estimacion_grasa_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='perfilusuario',
            name='disponibilidad_completa',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='perfilusuario',
            name='composicion_corporal_completa',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='perfilusuario',
            name='meta_fisica_opcion',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='perfilusuario',
            name='meta_fisica_aceptada',
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='RegistroProgresoPeso',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('peso', models.DecimalField(decimal_places=2, max_digits=5, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(500)])),
                ('porcentaje_grasa_estimado', models.DecimalField(blank=True, decimal_places=1, max_digits=4, null=True, validators=[django.core.validators.MinValueValidator(2), django.core.validators.MaxValueValidator(60)])),
                ('es_inicial', models.BooleanField(default=False)),
                ('progreso_percibido', models.CharField(blank=True, choices=[('avanzando', 'Sí, noto avances'), ('estable', 'Me siento igual'), ('dificil', 'Me está costando avanzar'), ('incierto', 'No estoy seguro/a')], default='', max_length=12)),
                ('adherencia_entrenamiento', models.CharField(blank=True, choices=[('todas', 'Todas o casi todas'), ('mayoria', 'La mayoría'), ('algunas', 'Algunas'), ('pocas', 'Pocas o ninguna')], default='', max_length=12)),
                ('adherencia_alimentacion', models.CharField(blank=True, choices=[('todas', 'Todas o casi todas'), ('mayoria', 'La mayoría'), ('algunas', 'Algunas'), ('pocas', 'Pocas o ninguna')], default='', max_length=12)),
                ('descanso', models.CharField(blank=True, choices=[('bueno', 'Bueno'), ('variable', 'Variable'), ('bajo', 'Insuficiente para mí')], default='', max_length=12)),
                ('estres', models.CharField(blank=True, choices=[('bajo', 'Bajo'), ('moderado', 'Moderado'), ('alto', 'Alto')], default='', max_length=12)),
                ('molestias_o_lesiones', models.BooleanField(blank=True, null=True)),
                ('creado', models.DateTimeField(auto_now_add=True)),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='registros_progreso_peso', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Registro de progreso de peso',
                'verbose_name_plural': 'Registros de progreso de peso',
                'ordering': ['-creado', '-pk'],
            },
        ),
        migrations.RunPython(preserve_existing_onboarding, migrations.RunPython.noop),
    ]
