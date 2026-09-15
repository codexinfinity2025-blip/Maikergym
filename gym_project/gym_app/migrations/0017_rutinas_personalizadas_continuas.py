from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("gym_app", "0016_enfoque_corporal")]

    operations = [
        migrations.AlterField(
            model_name="planentrenamiento",
            name="duracion_semanas",
            field=models.PositiveSmallIntegerField(
                default=12,
                validators=[MinValueValidator(1), MaxValueValidator(9999)],
            ),
        ),
        migrations.AlterField(
            model_name="faseplan",
            name="semana_inicio",
            field=models.PositiveSmallIntegerField(
                validators=[MinValueValidator(1), MaxValueValidator(9999)],
            ),
        ),
        migrations.AlterField(
            model_name="faseplan",
            name="semana_fin",
            field=models.PositiveSmallIntegerField(
                validators=[MinValueValidator(1), MaxValueValidator(9999)],
            ),
        ),
        migrations.AlterField(
            model_name="sesionentrenamiento",
            name="semana_plan",
            field=models.PositiveSmallIntegerField(
                validators=[MinValueValidator(1), MaxValueValidator(9999)],
            ),
        ),
    ]
