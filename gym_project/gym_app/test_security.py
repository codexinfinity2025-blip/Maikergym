from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse


class SeguridadTest(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(username='seguridad', email='seguridad@example.com', password='Original-Segura-746!')
        self.client.force_login(self.usuario)

    def test_cambiar_password_requiere_actual_y_cierra_otra_sesion(self):
        otra = Client()
        otra.force_login(self.usuario)
        url = reverse('cambiar_password')
        datos = {'old_password': 'incorrecta', 'new_password1': 'Nueva-Segura-937!', 'new_password2': 'Nueva-Segura-937!'}
        self.assertEqual(self.client.post(url, datos).status_code, 200)
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password('Original-Segura-746!'))
        datos['old_password'] = 'Original-Segura-746!'
        self.assertEqual(self.client.post(url, datos).status_code, 302)
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password('Nueva-Segura-937!'))
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(otra.get(url).status_code, 302)

    def test_csrf_y_password_debil(self):
        protegida = Client(enforce_csrf_checks=True)
        protegida.force_login(self.usuario)
        self.assertEqual(protegida.post(reverse('cambiar_password'), {}).status_code, 403)
        self.client.post(reverse('cambiar_password'), {'old_password':'Original-Segura-746!', 'new_password1':'123', 'new_password2':'123'})
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password('Original-Segura-746!'))

    def test_limite_intentos(self):
        self.client.logout()
        for _ in range(10):
            self.client.post(reverse('login'), {'email':'seguridad@example.com','password':'incorrecta'})
        self.assertEqual(self.client.post(reverse('login'), {'email':'seguridad@example.com','password':'incorrecta'}).status_code, 429)
