import json
from io import StringIO
from unittest.mock import patch, MagicMock
from urllib.error import HTTPError, URLError
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.management import call_command
from django.urls import reverse
from .email_delivery import DeliveryError, configuration_errors


@override_settings(EMAIL_BACKEND='gym_project.gym_app.email_delivery.ResendBackend', RESEND_API_KEY='test-private-key', DEFAULT_FROM_EMAIL='MaikerGym <access@example.com>', PUBLIC_BASE_URL='https://gym.example.com')
class EmailDeliveryTest(TestCase):
    def mock_response(self, opener):
        opener.return_value.__enter__.return_value.read.return_value = b'{"id":"accepted"}'

    @patch('gym_project.gym_app.email_delivery.urlopen')
    def test_https_reset_complete_flow(self, opener):
        self.mock_response(opener)
        user = User.objects.create_user('api-test', email='user@example.com', password='Previous-password-234!')
        response = self.client.post(reverse('password_reset'), {'email': user.email})
        self.assertEqual(response.status_code, 302)
        request = opener.call_args.args[0]
        self.assertEqual(request.full_url, 'https://api.resend.com/emails')
        payload = json.loads(request.data)
        self.assertEqual(payload['to'], [user.email])
        import re
        link = re.search(r'https://gym.example.com([^\s]+)', payload['text']).group(1)
        confirmation = self.client.get(link).url
        response = self.client.post(confirmation, {'new_password1': 'New-password-289!', 'new_password2': 'New-password-289!'})
        self.assertEqual(response.status_code, 302)
        user.refresh_from_db()
        self.assertTrue(user.check_password('New-password-289!'))
        self.assertContains(self.client.get(link), 'ya se utilizó')

    @patch('gym_project.gym_app.email_delivery.urlopen')
    def test_provider_failure_redacts_secrets(self, opener):
        opener.side_effect = HTTPError('https://api.resend.com/emails', 403, 'sensitive details', {}, None)
        with self.assertRaisesMessage(DeliveryError, 'PROVIDER_HTTP_403'):
            send_mail('Test', 'Private token', None, ['user@example.com'])

    @patch('gym_project.gym_app.email_delivery.urlopen')
    def test_connection_failure(self, opener):
        opener.side_effect = URLError('sensitive details')
        with self.assertRaisesMessage(DeliveryError, 'PROVIDER_CONNECTION_FAILED'):
            send_mail('Test', 'Private token', None, ['user@example.com'])

    @override_settings(RESEND_API_KEY='')
    def test_missing_key_same_status_for_all_accounts(self):
        User.objects.create_user('known', email='known@example.com')
        for email in ['known@example.com', 'unknown@example.com']:
            self.assertEqual(self.client.post(reverse('password_reset'), {'email': email}).status_code, 503)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend', EMAIL_HOST='smtp.gmail.com', EMAIL_HOST_USER='sender', EMAIL_HOST_PASSWORD='private', RAILWAY_SMTP_ENABLED=False)
    @patch.dict('os.environ', {'RAILWAY_ENVIRONMENT_ID': 'test'})
    def test_railway_smtp_guard(self):
        self.assertIn('RAILWAY_SMTP_REQUIRES_PRO_OR_HTTPS', configuration_errors())

    @patch('gym_project.gym_app.email_delivery.urlopen')
    def test_diagnostics_does_not_send_without_explicit_recipient(self, opener):
        output = StringIO()
        call_command('verificar_correo', stdout=output)
        opener.assert_not_called()
        self.assertNotIn('test-private-key', output.getvalue())

    @override_settings(PUBLIC_BASE_URL='https://gym.example.com/invalid/path')
    def test_rejects_origin_path(self):
        self.assertIn('PUBLIC_BASE_URL_INVALID', configuration_errors())
