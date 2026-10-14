from datetime import date
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase
from django.contrib.auth.models import User
from django.urls import reverse

from .profile_validation import validar_fecha_nacimiento


class EdadMinimaTest(SimpleTestCase):
    def test_cumpleanos_14_aceptado(self):
        self.assertEqual(validar_fecha_nacimiento('2012-10-07', date(2026, 10, 7)), date(2012, 10, 7))

    def test_un_dia_antes_de_14_rechazado(self):
        with self.assertRaisesMessage(ValidationError, 'desde los 14'):
            validar_fecha_nacimiento('2012-10-08', date(2026, 10, 7))

    def test_fecha_futura_o_invalida(self):
        for value in ('2027-01-01', 'abc', '', None, '2012-02-30'):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                validar_fecha_nacimiento(value, date(2026, 10, 7))

    def test_cumpleanos_bisiesto(self):
        with self.assertRaises(ValidationError):
            validar_fecha_nacimiento('2012-02-29', date(2026, 2, 28))
        self.assertEqual(validar_fecha_nacimiento('2012-02-29', date(2026, 3, 1)), date(2012, 2, 29))

    def test_no_se_impone_tope_del_modelo_3d_al_registro(self):
        self.assertEqual(validar_fecha_nacimiento('1930-01-01', date(2026, 10, 7)), date(1930, 1, 1))


class RegistroEdadTest(TestCase):
    def datos(self, birth):
        return {'nombre': 'Prueba', 'apellido': 'Edad', 'email': 'edad@example.com',
                'password': 'Prueba-Edad-784!', 'confirmar_password': 'Prueba-Edad-784!',
                'fecha_nacimiento': birth, 'enfoque_corporal': 'full_body'}

    @patch('gym_project.gym_app.profile_validation.timezone.localdate', return_value=date(2026, 10, 7))
    def test_post_menor_no_crea_cuenta(self, _today):
        response = self.client.post(reverse('registrarse'), {
            'nombre': 'Prueba', 'apellido': 'Edad', 'email': 'edad@example.com',
            'password': 'Prueba-Edad-784!', 'confirmar_password': 'Prueba-Edad-784!',
            'fecha_nacimiento': '2012-10-08', 'enfoque_corporal': 'full_body',
        })
        self.assertContains(response, 'desde los 14 años')
        self.assertFalse(User.objects.filter(username='edad@example.com').exists())

    @patch('gym_project.gym_app.profile_validation.timezone.localdate', return_value=date(2026, 10, 7))
    def test_registro_justo_14_y_revision_no_permite_menor(self, _today):
        response = self.client.post(reverse('registrarse'), self.datos('2012-10-07'))
        self.assertRedirects(response, reverse('revisar_registro'))
        user = User.objects.get(username='edad@example.com')
        self.assertEqual(user.perfil.edad, 14)
        response = self.client.post(reverse('revisar_registro'), self.datos('2012-10-08'))
        self.assertContains(response, 'desde los 14 años')
        user.perfil.refresh_from_db()
        self.assertEqual(user.perfil.fecha_nacimiento, date(2012, 10, 7))

    @patch('gym_project.gym_app.profile_validation.timezone.localdate', return_value=date(2026, 10, 7))
    def test_datos_personales_no_elude_edad_minima(self, _today):
        user=User.objects.create_user('personal@example.com', password='Prueba-Edad-784!')
        perfil=user.perfil
        perfil.objetivo='salud'
        perfil.nivel_declarado='principiante'
        perfil.nivel_entrenamiento='principiante'
        perfil.prueba_nivel_completada=True
        perfil.configuracion_entrenamiento_completa=True
        perfil.orientacion_nutricional_vista=True
        perfil.fecha_nacimiento=date(2000,1,1)
        perfil.save()
        self.client.force_login(user)
        response=self.client.post(reverse('datos_personales'), {
            'genero':'masculino','peso':'60','altura_cm':'165','fecha_nacimiento':'2012-10-08'})
        self.assertEqual(response.status_code,400)
        perfil.refresh_from_db()
        self.assertEqual(perfil.fecha_nacimiento,date(2000,1,1))
