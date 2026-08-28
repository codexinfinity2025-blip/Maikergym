from datetime import date

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import (
    AsignacionPlanUsuario,
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
