# Generated manually for MaikerGym personalization flow

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gym_app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='perfilusuario',
            name='datos_completos',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='perfilusuario',
            name='dieta_aceptada',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='perfilusuario',
            name='edad',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='perfilusuario',
            name='foto',
            field=models.ImageField(blank=True, null=True, upload_to='perfiles/'),
        ),
        migrations.AddField(
            model_name='perfilusuario',
            name='genero',
            field=models.CharField(blank=True, choices=[('femenino', 'Femenino'), ('masculino', 'Masculino'), ('otro', 'Otro')], max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='perfilusuario',
            name='peso',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
    ]