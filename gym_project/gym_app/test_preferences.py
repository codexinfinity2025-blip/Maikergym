from django.test import TestCase
from django.contrib.auth.models import User
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone
from .models import PerfilUsuario
from .services import crear_rutina_automatica, iniciar_sesion_entrenamiento


class PreferencesTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('cargar_ejercicios', verbosity=0)

    def setUp(self):
        self.user = User.objects.create_user(username='preferencias')
        self.perfil = PerfilUsuario.objects.get(user=self.user)
        self.perfil.objetivo = 'salud'
        self.perfil.nivel_entrenamiento = self.perfil.nivel_declarado = 'principiante'
        self.perfil.modalidad_rutina = 'automatica'
        self.perfil.dias_entrenamiento = [0, 2, 4]
        self.perfil.save()
        self.client.force_login(self.user)
        self.data = {'peso': '75.50', 'altura_cm': '175', 'genero': 'masculino', 'enfoque_corporal': 'superior'}

    def test_save_and_validation(self):
        response = self.client.get(reverse('preferencias'))
        self.assertContains(response, 'Guardar mis datos y preferencias')
        self.assertEqual(self.client.post(reverse('preferencias'), self.data).status_code, 302)
        self.perfil.refresh_from_db()
        self.assertEqual(self.perfil.enfoque_corporal, 'superior')
        self.assertEqual(float(self.perfil.altura_cm), 175)
        bad = dict(self.data, altura_cm='400', enfoque_corporal='inventado')
        self.assertEqual(self.client.post(reverse('preferencias'), bad).status_code, 200)
        self.perfil.refresh_from_db()
        self.assertEqual(float(self.perfil.altura_cm), 175)

    def test_regenerate_before_first_session(self):
        old = crear_rutina_automatica(self.user, 'salud', 'principiante', [0, 2, 4], 60, 60)
        response = self.client.post(reverse('preferencias'), self.data)
        self.assertEqual(response.status_code, 302)
        active = self.user.planes_asignados.get(estado='activo')
        self.assertNotEqual(active.pk, old.pk)
        self.assertEqual(active.fase_actual.dias.order_by('numero').first().nombre, 'Pecho, hombros y tríceps')

    def test_preserve_started_plan(self):
        old = crear_rutina_automatica(self.user, 'salud', 'principiante', [timezone.localdate().weekday()], 60, 60)
        iniciar_sesion_entrenamiento(old, old.fase_actual.dias.order_by('numero').first())
        self.assertEqual(self.client.post(reverse('preferencias'), self.data).status_code, 302)
        self.assertEqual(self.user.planes_asignados.get(estado='activo').pk, old.pk)
        self.assertContains(self.client.get(reverse('preferencias')), 'Ya iniciaste')

    def test_requires_authentication(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse('preferencias')).status_code, 302)
