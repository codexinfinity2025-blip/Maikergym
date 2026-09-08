from django.db import migrations, models


def conservar_enfoque(apps, schema_editor):
    apps.get_model('gym_app', 'PerfilUsuario').objects.filter(priorizar_tren_inferior=True).update(enfoque_corporal='inferior')


class Migration(migrations.Migration):
    dependencies = [('gym_app', '0015_limiteacceso')]
    operations = [
        migrations.AddField(model_name='perfilusuario', name='enfoque_corporal', field=models.CharField(max_length=20, choices=[('inferior', 'Tren inferior'), ('superior', 'Tren superior'), ('full_body', 'Full body · cuerpo completo')], default='full_body')),
        migrations.RunPython(conservar_enfoque, migrations.RunPython.noop),
    ]
