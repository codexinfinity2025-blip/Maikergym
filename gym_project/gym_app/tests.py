from datetime import date

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import (
    AsignacionPlanUsuario,
    Ejercicio,
    EstadoAsignacionChoice,
    ObjetivoChoice,
    PerfilUsuario,
    PlanEntrenamiento,
)


class FlujoRegistroTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("cargar_ejercicios", verbosity=0)
        call_command("cargar_plan_hipertrofia", verbosity=0)

    def test_hay_un_plan_inicial_para_cada_objetivo(self):
        objetivos_disponibles = set(
            PlanEntrenamiento.objects.filter(
                activo=True,
            ).values_list("objetivo", flat=True)
        )
        self.assertEqual(
            objetivos_disponibles,
            set(ObjetivoChoice.values),
        )

    def test_catalogo_ampliado_y_planes_con_rutinas_propias(self):
        nuevos = {
            "Sentadilla goblet con mancuerna",
            "Zancada estática con mancuernas",
            "Step-up al banco",
            "Puente de glúteos en suelo",
            "Press de pecho sentado en máquina",
            "Face pull en polea",
            "Curl de bíceps en polea baja",
            "Extensión de tríceps sobre la cabeza en polea",
            "Press Pallof en polea",
            "Bird dog",
        }
        self.assertEqual(Ejercicio.objects.count(), 36)
        self.assertEqual(
            set(
                Ejercicio.objects.filter(nombre__in=nuevos)
                .values_list("nombre", flat=True)
            ),
            nuevos,
        )

        planes = {
            plan.objetivo: plan
            for plan in PlanEntrenamiento.objects.filter(activo=True)
        }
        self.assertEqual(len(planes), 4)
        for objetivo in ObjetivoChoice.values:
            plan = planes[objetivo]
            self.assertEqual(plan.fases.filter(activo=True).count(), 3)
            for fase in plan.fases.filter(activo=True):
                self.assertEqual(fase.dias.filter(activo=True).count(), 3)
                for dia in fase.dias.filter(activo=True):
                    self.assertEqual(
                        dia.ejercicios_programados.filter(activo=True).count(),
                        6,
                    )

        ejercicios_estetica = set(
            planes[ObjetivoChoice.ESTETICO]
            .fases.filter(orden=1)
            .values_list(
                "dias__ejercicios_programados__ejercicio__nombre",
                flat=True,
            )
        )
        ejercicios_salud = set(
            planes[ObjetivoChoice.SALUD]
            .fases.filter(orden=1)
            .values_list(
                "dias__ejercicios_programados__ejercicio__nombre",
                flat=True,
            )
        )
        ejercicios_perder_peso = set(
            planes[ObjetivoChoice.PERDER_PESO]
            .fases.filter(orden=1)
            .values_list(
                "dias__ejercicios_programados__ejercicio__nombre",
                flat=True,
            )
        )
        self.assertTrue(nuevos.intersection(ejercicios_estetica))
        self.assertTrue(nuevos.intersection(ejercicios_salud))
        self.assertTrue(nuevos.intersection(ejercicios_perder_peso))
        self.assertNotEqual(ejercicios_estetica, ejercicios_salud)
        self.assertNotEqual(ejercicios_estetica, ejercicios_perder_peso)
        self.assertNotEqual(ejercicios_salud, ejercicios_perder_peso)
        self.assertIn(
            "Caminata inclinada en caminadora",
            ejercicios_perder_peso,
        )
        self.assertIn(
            "Remo en máquina ergométrica",
            ejercicios_perder_peso,
        )

        call_command("cargar_plan_hipertrofia", verbosity=0)
        self.assertEqual(
            PlanEntrenamiento.objects.filter(activo=True).count(),
            4,
        )
        for plan in PlanEntrenamiento.objects.filter(activo=True):
            self.assertEqual(
                plan.fases.filter(
                    activo=True,
                    dias__activo=True,
                    dias__ejercicios_programados__activo=True,
                ).distinct().count(),
                3,
            )

    def test_perder_peso_se_puede_elegir_y_asigna_su_plan(self):
        usuario = User.objects.create_user(
            username="perder-peso@example.com",
            email="perder-peso@example.com",
            password="ClaveSegura2026!",
        )
        self.client.force_login(usuario)

        respuesta = self.client.post(
            reverse("objetivo"),
            {"objetivo": ObjetivoChoice.PERDER_PESO},
        )

        self.assertRedirects(
            respuesta,
            reverse("dieta"),
            fetch_redirect_response=False,
        )
        perfil = PerfilUsuario.objects.get(user=usuario)
        self.assertEqual(
            perfil.objetivo,
            ObjetivoChoice.PERDER_PESO,
        )
        asignacion = AsignacionPlanUsuario.objects.get(
            usuario=usuario,
            estado=EstadoAsignacionChoice.ACTIVO,
        )
        self.assertEqual(
            asignacion.plan.objetivo,
            ObjetivoChoice.PERDER_PESO,
        )

    def test_registro_no_repite_datos_y_llega_al_entrenamiento(self):
        respuesta = self.client.post(
            reverse("registrarse"),
            {
                "nombre": "Prueba",
                "apellido": "MaikerGym",
                "telefono": "3001234567",
                "direccion": "Calle de prueba 123",
                "email": "flujo@example.com",
                "password": "ClaveSegura2026!",
                "confirmar_password": "ClaveSegura2026!",
                "fecha_nacimiento": "2000-05-20",
            },
        )
        self.assertRedirects(
            respuesta,
            reverse("objetivo"),
            fetch_redirect_response=False,
        )

        usuario = User.objects.get(email="flujo@example.com")
        perfil = PerfilUsuario.objects.get(user=usuario)
        self.assertEqual(perfil.fecha_nacimiento, date(2000, 5, 20))
        self.assertEqual(perfil.telefono, "3001234567")
        self.assertEqual(perfil.direccion, "Calle de prueba 123")

        respuesta = self.client.post(
            reverse("objetivo"),
            {"objetivo": ObjetivoChoice.ESTETICO},
        )
        self.assertRedirects(
            respuesta,
            reverse("dieta"),
            fetch_redirect_response=False,
        )

        respuesta = self.client.post(
            reverse("dieta"),
            {"acepta_dieta": "on"},
        )
        self.assertRedirects(
            respuesta,
            reverse("datos_personales"),
            fetch_redirect_response=False,
        )

        respuesta = self.client.post(
            reverse("datos_personales"),
            {
                "genero": "masculino",
                "peso": "72.50",
            },
        )
        self.assertRedirects(
            respuesta,
            reverse("mi_entrenamiento"),
            fetch_redirect_response=False,
        )

        perfil.refresh_from_db()
        self.assertTrue(perfil.personalizacion_completa())
        asignacion = AsignacionPlanUsuario.objects.get(
            usuario=usuario,
            estado=EstadoAsignacionChoice.ACTIVO,
        )
        self.assertEqual(
            asignacion.plan.objetivo,
            ObjetivoChoice.ESTETICO,
        )

        respuesta = self.client.post(
            reverse("objetivo"),
            {"objetivo": ObjetivoChoice.ESTETICO},
        )
        self.assertRedirects(
            respuesta,
            reverse("mi_entrenamiento"),
            fetch_redirect_response=False,
        )
        perfil.refresh_from_db()
        self.assertTrue(perfil.dieta_aceptada)
        self.assertTrue(perfil.datos_completos)
