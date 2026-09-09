import base64
import json
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError
from django.test import SimpleTestCase, override_settings
from django.core.mail import send_mail
from .email_delivery import DeliveryError, configuration_errors


@override_settings(EMAIL_BACKEND='gym_project.gym_app.email_delivery.GmailBackend',
    GMAIL_CLIENT_ID='test-id', GMAIL_CLIENT_SECRET='test-secret', GMAIL_REFRESH_TOKEN='test-refresh',
    DEFAULT_FROM_EMAIL='MaikerGym <sender@gmail.com>', PUBLIC_BASE_URL='https://gym.example.com')
class GmailDeliveryTest(SimpleTestCase):
    def response(self, data):
        result = MagicMock()
        result.__enter__.return_value.read.return_value = json.dumps(data).encode()
        return result

    @patch('gym_project.gym_app.email_delivery.urlopen')
    def test_https_message_and_refresh(self, opener):
        opener.side_effect = [self.response({'access_token': 'test-access'}), self.response({'id': 'accepted'})]
        self.assertEqual(send_mail('Recuperación', 'Private reset link', None, ['user@example.com']), 1)
        auth, send = [call.args[0] for call in opener.call_args_list]
        self.assertEqual(auth.full_url, 'https://oauth2.googleapis.com/token')
        self.assertIn(b'grant_type=refresh_token', auth.data)
        self.assertEqual(send.full_url, 'https://gmail.googleapis.com/gmail/v1/users/me/messages/send')
        self.assertEqual(send.headers['Authorization'], 'Bearer test-access')
        raw = base64.urlsafe_b64decode(json.loads(send.data)['raw'])
        self.assertIn(b'To: user@example.com', raw)
        self.assertIn(b'Private reset link', raw)
        self.assertEqual(configuration_errors(), [])

    @patch('gym_project.gym_app.email_delivery.urlopen')
    def test_auth_failure_is_redacted_and_no_send(self, opener):
        opener.side_effect = HTTPError('https://oauth2.googleapis.com/token', 400, 'private token details', {}, None)
        with self.assertRaisesMessage(DeliveryError, 'GMAIL_AUTH_HTTP_400'):
            send_mail('Test', 'body', None, ['user@example.com'])
        self.assertEqual(opener.call_count, 1)

    @override_settings(GMAIL_REFRESH_TOKEN='')
    @patch('gym_project.gym_app.email_delivery.urlopen')
    def test_missing_config_no_network(self, opener):
        self.assertIn('GMAIL_OAUTH_CONFIG_MISSING', configuration_errors())
        self.assertEqual(send_mail('Test', 'body', None, ['user@example.com'], fail_silently=True), 0)
        opener.assert_not_called()

    @patch('gym_project.gym_app.email_delivery.urlopen')
    def test_no_retry_of_uncertain_delivery(self, opener):
        opener.side_effect = [self.response({'access_token': 'test-access'}), TimeoutError()]
        with self.assertRaisesMessage(DeliveryError, 'GMAIL_SEND_CONNECTION_FAILED'):
            send_mail('Test', 'body', None, ['user@example.com'])
        self.assertEqual(opener.call_count, 2)

    @patch('gym_project.gym_app.email_delivery.urlopen')
    def test_invalid_token_response(self, opener):
        opener.return_value = self.response({})
        with self.assertRaisesMessage(DeliveryError, 'GMAIL_AUTH_RESPONSE_INVALID'):
            send_mail('Test', 'body', None, ['user@example.com'])
