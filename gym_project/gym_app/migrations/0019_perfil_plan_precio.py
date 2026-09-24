from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('gym_app', '0018_sesion_fecha_programada')]
    operations = [migrations.AddField(
        model_name='perfilusuario', name='plan_precio',
        field=models.CharField(blank=True, default='', max_length=20, choices=[
            ('mensual', 'Mensual'), ('semestral', 'Semestral'), ('premium_anual', 'Premium anual')]),
    )]
