from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from .models import PerfilUsuario


class RegistrationReviewTest(TestCase):
    def test_registration_page_renders_without_profile(self):
        response = self.client.get(reverse('registrarse'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cuerpo completo · trabajo equilibrado')

    def test_review_after_registration_and_edit(self):
        data = {'nombre': 'Ana', 'apellido': 'Prueba', 'email': 'review@example.com',
                'password': 'Secure-Example-583!', 'confirmar_password': 'Secure-Example-583!',
                'fecha_nacimiento': '2000-01-01', 'enfoque_corporal': 'superior'}
        self.assertRedirects(self.client.post(reverse('registrarse'), data), reverse('revisar_registro'))
        self.assertContains(self.client.get(reverse('revisar_registro')), 'review@example.com')
        changed = dict(data, nombre='Andrea', fecha_nacimiento='2001-02-03', enfoque_corporal='inferior')
        self.assertRedirects(self.client.post(reverse('revisar_registro'), changed), reverse('objetivo'))
        user = User.objects.get(email='review@example.com')
        self.assertEqual(user.first_name, 'Andrea')
        self.assertEqual(PerfilUsuario.objects.get(user=user).enfoque_corporal, 'inferior')
        self.assertEqual(User.objects.count(), 1)
        changed['email'] = 'other@example.com'
        self.assertEqual(self.client.post(reverse('revisar_registro'), changed).status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.email, 'review@example.com')
        changed['password_actual'] = data['password']
        self.assertRedirects(self.client.post(reverse('revisar_registro'), changed), reverse('objetivo'))
        user.refresh_from_db()
        self.assertEqual(user.email, 'other@example.com')

    def test_login_required(self):
        self.assertEqual(self.client.get(reverse('revisar_registro')).status_code, 302)
