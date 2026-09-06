from django.db import migrations, models


NOMBRE_NUTRICION = "Nutrición y acondicionamiento de 12 semanas"
NOMBRE_PERDER_PESO = "Pérdida de peso inicial de 12 semanas"
SLUG_PERDER_PESO = "perdida-de-peso-inicial-de-12-semanas"


def migrar_objetivos_anteriores(apps, schema_editor):
    PerfilUsuario = apps.get_model("gym_app", "PerfilUsuario")
    PlanEntrenamiento = apps.get_model(
        "gym_app",
        "PlanEntrenamiento",
    )
    AsignacionPlanUsuario = apps.get_model(
        "gym_app",
        "AsignacionPlanUsuario",
    )

    PerfilUsuario.objects.filter(objetivo="nutricion").update(
        objetivo="perder_peso",
    )
    PerfilUsuario.objects.filter(objetivo="recuperar").update(
        objetivo="salud",
    )

    plan_nutricion = PlanEntrenamiento.objects.filter(
        nombre=NOMBRE_NUTRICION,
    ).first()
    plan_perder_peso = PlanEntrenamiento.objects.filter(
        nombre=NOMBRE_PERDER_PESO,
    ).first()

    PlanEntrenamiento.objects.filter(objetivo="nutricion").update(
        objetivo="perder_peso",
    )

    if plan_nutricion is not None and plan_perder_peso is None:
        plan_nutricion.nombre = NOMBRE_PERDER_PESO
        plan_nutricion.slug = SLUG_PERDER_PESO
        plan_nutricion.objetivo = "perder_peso"
        plan_nutricion.save(
            update_fields=["nombre", "slug", "objetivo"],
        )
    elif plan_nutricion is not None:
        plan_nutricion.activo = False
        plan_nutricion.save(update_fields=["activo"])

    planes_recuperacion = PlanEntrenamiento.objects.filter(
        objetivo="recuperar",
    )
    ids_recuperacion = list(
        planes_recuperacion.values_list("id", flat=True),
    )
    if ids_recuperacion:
        AsignacionPlanUsuario.objects.filter(
            plan_id__in=ids_recuperacion,
            estado="activo",
        ).update(estado="abandonado")
        planes_recuperacion.update(objetivo="salud", activo=False)


def revertir_objetivos(apps, schema_editor):
    PerfilUsuario = apps.get_model("gym_app", "PerfilUsuario")
    PlanEntrenamiento = apps.get_model(
        "gym_app",
        "PlanEntrenamiento",
    )

    PerfilUsuario.objects.filter(objetivo="perder_peso").update(
        objetivo="nutricion",
    )
    PlanEntrenamiento.objects.filter(objetivo="perder_peso").update(
        objetivo="nutricion",
    )

    plan_perder_peso = PlanEntrenamiento.objects.filter(
        nombre=NOMBRE_PERDER_PESO,
    ).first()
    if (
        plan_perder_peso is not None
        and not PlanEntrenamiento.objects.filter(
            nombre=NOMBRE_NUTRICION,
        ).exists()
    ):
        plan_perder_peso.nombre = NOMBRE_NUTRICION
        plan_perder_peso.slug = (
            "nutricion-y-acondicionamiento-de-12-semanas"
        )
        plan_perder_peso.save(update_fields=["nombre", "slug"])


class Migration(migrations.Migration):

    dependencies = [
        ("gym_app", "0009_serieejerciciosesion_and_more"),
    ]

    operations = [
        migrations.RunPython(
            migrar_objetivos_anteriores,
            revertir_objetivos,
        ),
        migrations.AlterField(
            model_name="perfilusuario",
            name="objetivo",
            field=models.CharField(
                blank=True,
                choices=[
                    ("estetico", "Estético"),
                    ("hipertrofia", "Hipertrofia"),
                    ("salud", "Salud"),
                    ("perder_peso", "Pérdida de peso"),
                ],
                max_length=50,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="planentrenamiento",
            name="objetivo",
            field=models.CharField(
                choices=[
                    ("estetico", "Estético"),
                    ("hipertrofia", "Hipertrofia"),
                    ("salud", "Salud"),
                    ("perder_peso", "Pérdida de peso"),
                ],
                max_length=20,
            ),
        ),
    ]
