from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models
import django.db.models.deletion


def conservar_configuracion_existente(apps, schema_editor):
    PerfilUsuario = apps.get_model("gym_app", "PerfilUsuario")
    AsignacionPlanUsuario = apps.get_model("gym_app", "AsignacionPlanUsuario")

    for perfil in PerfilUsuario.objects.all().iterator():
        asignacion = (
            AsignacionPlanUsuario.objects
            .filter(usuario_id=perfil.user_id, estado="activo")
            .first()
        )
        perfil.nivel_declarado = "principiante"
        perfil.nivel_entrenamiento = "principiante"
        perfil.prueba_nivel_completada = True
        perfil.orientacion_nutricional_vista = perfil.dieta_aceptada
        if asignacion is not None:
            dias = list(
                asignacion.horarios.filter(activo=True)
                .order_by("numero_dia_plan")
                .values_list("dia_semana", flat=True)
            )
            perfil.dias_entrenamiento = dias or [0, 2, 4]
            perfil.modalidad_rutina = "automatica"
            perfil.configuracion_entrenamiento_completa = True
        perfil.save()


class Migration(migrations.Migration):

    dependencies = [
        ("gym_app", "0010_cuatro_objetivos_perdida_peso"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="perfilusuario",
            name="minutos_por_dia",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="perfilusuario",
            name="aviso_rutina_personalizada_aceptado",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="perfilusuario",
            name="configuracion_entrenamiento_completa",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="perfilusuario",
            name="descanso_preferido_segundos",
            field=models.PositiveSmallIntegerField(
                default=60,
                validators=[MinValueValidator(15), MaxValueValidator(1800)],
            ),
        ),
        migrations.AddField(
            model_name="perfilusuario",
            name="dias_entrenamiento",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="perfilusuario",
            name="duracion_sesion_minutos",
            field=models.PositiveIntegerField(
                default=60,
                validators=[MinValueValidator(45)],
            ),
        ),
        migrations.AddField(
            model_name="perfilusuario",
            name="modalidad_rutina",
            field=models.CharField(
                blank=True,
                choices=[
                    ("automatica", "Rutina recomendada por MaikerGym"),
                    ("personalizada", "Crear mi propia rutina"),
                ],
                max_length=20,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="perfilusuario",
            name="nivel_declarado",
            field=models.CharField(
                blank=True,
                choices=[
                    ("principiante", "Principiante"),
                    ("intermedio", "Intermedio"),
                    ("encima_promedio", "Encima del promedio"),
                    ("avanzado", "Avanzado"),
                ],
                max_length=20,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="perfilusuario",
            name="nivel_entrenamiento",
            field=models.CharField(
                blank=True,
                choices=[
                    ("principiante", "Principiante"),
                    ("intermedio", "Intermedio"),
                    ("encima_promedio", "Encima del promedio"),
                    ("avanzado", "Avanzado"),
                ],
                max_length=20,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="perfilusuario",
            name="orientacion_nutricional_vista",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="perfilusuario",
            name="prueba_nivel_completada",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="perfilusuario",
            name="puntuacion_prueba_nivel",
            field=models.PositiveSmallIntegerField(
                blank=True,
                null=True,
                validators=[MaxValueValidator(30)],
            ),
        ),
        migrations.AddField(
            model_name="planentrenamiento",
            name="es_personalizado",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="planentrenamiento",
            name="propietario",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="rutinas_personalizadas",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="ejercicio",
            name="nivel",
            field=models.CharField(
                choices=[
                    ("principiante", "Principiante"),
                    ("intermedio", "Intermedio"),
                    ("encima_promedio", "Encima del promedio"),
                    ("avanzado", "Avanzado"),
                ],
                default="principiante",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="planentrenamiento",
            name="nivel",
            field=models.CharField(
                choices=[
                    ("principiante", "Principiante"),
                    ("intermedio", "Intermedio"),
                    ("encima_promedio", "Encima del promedio"),
                    ("avanzado", "Avanzado"),
                ],
                default="principiante",
                max_length=20,
            ),
        ),
        migrations.RunPython(
            conservar_configuracion_existente,
            migrations.RunPython.noop,
        ),
    ]
