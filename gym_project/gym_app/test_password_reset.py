import re
from datetime import timedelta
from unittest.mock import patch
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', DEFAULT_FROM_EMAIL='MaikerGym <noreply@example.com>', PUBLIC_BASE_URL='https://gym.example.com')
class RecuperacionTest(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(username='recuperacion', email='persona@example.com', password='Anterior-987!')

    def test_correo_token_un_solo_uso(self):
        self.assertEqual(self.client.post(reverse('password_reset'), {'email':'persona@example.com'}).status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        enlace = re.search(r'https://gym.example.com([^\s]+)', mail.outbox[0].body).group(1)
        uid = urlsafe_base64_encode(force_bytes(self.usuario.pk))
        token = enlace.rstrip('/').split('/')[-1]
        respuesta = self.client.get(enlace)
        self.assertEqual(respuesta.status_code, 302)
        confirmar = respuesta.url
        self.assertEqual(self.client.get(confirmar).status_code, 200)
        self.assertEqual(self.client.post(confirmar, {'new_password1':'Nueva-Privada-839!', 'new_password2':'Nueva-Privada-839!'}).status_code, 302)
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password('Nueva-Privada-839!'))
        self.assertFalse(default_token_generator.check_token(self.usuario, token))
        self.assertContains(self.client.get(enlace), 'ya se utilizó')

    def test_correo_desconocido_misma_respuesta(self):
        existente = self.client.post(reverse('password_reset'), {'email':'persona@example.com'})
        desconocido = self.client.post(reverse('password_reset'), {'email':'desconocido@example.com'})
        self.assertEqual(existente.status_code, desconocido.status_code)
        self.assertEqual(existente.url, desconocido.url)
        self.assertEqual(len(mail.outbox), 1)

    def test_token_caduca(self):
        token = default_token_generator.make_token(self.usuario)
        futuro = default_token_generator._now() + timedelta(seconds=1801)
        with patch.object(default_token_generator, '_now', return_value=futuro):
            self.assertFalse(default_token_generator.check_token(self.usuario, token))

    def test_https_real_csrf_reset_and_cross_origin_rejection(self):
        browser = Client(enforce_csrf_checks=True)
        uid = urlsafe_base64_encode(force_bytes(self.usuario.pk))
        token = default_token_generator.make_token(self.usuario)
        link = reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
        redirect = browser.get(link, secure=True)
        page = browser.get(redirect.url, secure=True)
        self.assertEqual(page['Referrer-Policy'], 'same-origin')
        csrf = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', page.content.decode()).group(1)
        fields = {'csrfmiddlewaretoken': csrf, 'new_password1': 'Nueva-Privada-839!', 'new_password2': 'Nueva-Privada-839!'}
        self.assertEqual(browser.post(redirect.url, fields, secure=True, HTTP_REFERER='https://evil.example/').status_code, 403)
        self.assertEqual(browser.post(redirect.url, fields, secure=True).status_code, 403)
        result = browser.post(redirect.url, fields, secure=True, HTTP_REFERER='https://testserver' + redirect.url)
        self.assertRedirects(result, reverse('password_reset_complete'), fetch_redirect_response=False)
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password('Nueva-Privada-839!'))
        self.assertFalse(default_token_generator.check_token(self.usuario, token))

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend', EMAIL_HOST='')
    def test_smtp_sin_configurar_no_finge_envio(self):
        self.assertEqual(self.client.post(reverse('password_reset'), {'email':'persona@example.com'}).status_code, 503)
