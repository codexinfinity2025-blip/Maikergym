"""HTTPS email delivery and diagnostics without logging secrets or reset links."""
import json
import base64
import os
from email.utils import parseaddr
from urllib.parse import urlsplit, urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend


class DeliveryError(Exception):
    pass


def configuration_errors():
    errors = []
    origin = urlsplit(settings.PUBLIC_BASE_URL)
    if (not origin.netloc or origin.username or origin.password or origin.query or origin.fragment
            or origin.path not in ('', '/') or origin.scheme not in ('http', 'https')
            or (not settings.DEBUG and origin.scheme != 'https')):
        errors.append('PUBLIC_BASE_URL_INVALID')
    backend = settings.EMAIL_BACKEND
    if not parseaddr(settings.DEFAULT_FROM_EMAIL)[1] or '@' not in parseaddr(settings.DEFAULT_FROM_EMAIL)[1]:
        errors.append('FROM_EMAIL_MISSING')
    if backend.endswith('smtp.EmailBackend'):
        if not settings.EMAIL_HOST or not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
            errors.append('SMTP_CONFIG_MISSING')
        if settings.EMAIL_USE_TLS and settings.EMAIL_USE_SSL:
            errors.append('SMTP_TLS_SSL_CONFLICT')
        if os.environ.get('RAILWAY_ENVIRONMENT_ID') and not settings.RAILWAY_SMTP_ENABLED:
            errors.append('RAILWAY_SMTP_REQUIRES_PRO_OR_HTTPS')
    elif backend == 'gym_project.gym_app.email_delivery.ResendBackend':
        if not settings.RESEND_API_KEY:
            errors.append('RESEND_API_KEY_MISSING')
    elif backend == 'gym_project.gym_app.email_delivery.GmailBackend':
        if not all((settings.GMAIL_CLIENT_ID, settings.GMAIL_CLIENT_SECRET, settings.GMAIL_REFRESH_TOKEN)):
            errors.append('GMAIL_OAUTH_CONFIG_MISSING')
    elif not settings.DEBUG and backend != 'django.core.mail.backends.locmem.EmailBackend':
        errors.append('EMAIL_BACKEND_UNSUPPORTED')
    return errors


class GmailBackend(BaseEmailBackend):
    """Send through HTTPS with a sender-authorized refresh token, never SMTP."""

    def _request(self, request, stage):
        try:
            with urlopen(request, timeout=settings.EMAIL_TIMEOUT) as response:
                result = json.loads(response.read(65536))
                if not isinstance(result, dict):
                    raise ValueError()
                return result
        except HTTPError as error:
            raise DeliveryError(stage + '_HTTP_' + str(error.code)) from None
        except (URLError, TimeoutError, OSError):
            raise DeliveryError(stage + '_CONNECTION_FAILED') from None
        except (ValueError, AttributeError):
            raise DeliveryError(stage + '_RESPONSE_INVALID') from None

    def send_messages(self, email_messages):
        sent = 0
        access_token = None
        for email in email_messages or []:
            if not email.recipients():
                continue
            try:
                if not all((settings.GMAIL_CLIENT_ID, settings.GMAIL_CLIENT_SECRET, settings.GMAIL_REFRESH_TOKEN)):
                    raise DeliveryError('GMAIL_OAUTH_CONFIG_MISSING')
                # This backend is for transactional mail, not blind-copy campaigns.
                if email.bcc:
                    raise DeliveryError('GMAIL_BCC_UNSUPPORTED')
                message = email.message()  # Validate headers before contacting Google.
                if access_token is None:
                    result = self._request(Request('https://oauth2.googleapis.com/token', method='POST',
                        data=urlencode({'client_id': settings.GMAIL_CLIENT_ID,
                            'client_secret': settings.GMAIL_CLIENT_SECRET,
                            'refresh_token': settings.GMAIL_REFRESH_TOKEN,
                            'grant_type': 'refresh_token'}).encode('utf-8'),
                        headers={'Content-Type': 'application/x-www-form-urlencoded'}), 'GMAIL_AUTH')
                    access_token = result.get('access_token')
                    if not isinstance(access_token, str) or not access_token or '\r' in access_token or '\n' in access_token:
                        raise DeliveryError('GMAIL_AUTH_RESPONSE_INVALID')
                raw = base64.urlsafe_b64encode(message.as_bytes(linesep='\r\n')).decode('ascii')
                result = self._request(Request('https://gmail.googleapis.com/gmail/v1/users/me/messages/send',
                    method='POST', data=json.dumps({'raw': raw}).encode('utf-8'),
                    headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + access_token}), 'GMAIL_SEND')
                if not result.get('id'):
                    raise DeliveryError('GMAIL_SEND_RESPONSE_INVALID')
                sent += 1
            except Exception:
                if not self.fail_silently:
                    raise
        return sent


class ResendBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        sent = 0
        for email in email_messages or []:
            if not email.recipients():
                continue
            try:
                if not settings.RESEND_API_KEY:
                    raise DeliveryError('RESEND_API_KEY_MISSING')
                if email.attachments:
                    raise DeliveryError('ATTACHMENTS_UNSUPPORTED')
                email.message()  # Validate header injection before contacting the provider.
                payload = {'from': email.from_email, 'to': email.to,
                           'subject': email.subject, 'text': email.body}
                if email.cc:
                    payload['cc'] = email.cc
                if email.bcc:
                    payload['bcc'] = email.bcc
                if email.reply_to:
                    payload['reply_to'] = email.reply_to
                for content, mime in getattr(email, 'alternatives', []):
                    if mime == 'text/html':
                        payload['html'] = content
                request = Request('https://api.resend.com/emails', method='POST',
                    data=json.dumps(payload).encode('utf-8'), headers={
                        'Authorization': 'Bearer ' + settings.RESEND_API_KEY,
                        'Content-Type': 'application/json', 'User-Agent': 'MaikerGym/1.0'})
                try:
                    with urlopen(request, timeout=settings.EMAIL_TIMEOUT) as response:
                        result = json.loads(response.read(65536))
                        if not result.get('id'):
                            raise DeliveryError('PROVIDER_RESPONSE_INVALID')
                except HTTPError as error:
                    raise DeliveryError('PROVIDER_HTTP_' + str(error.code)) from None
                except (URLError, TimeoutError, OSError):
                    raise DeliveryError('PROVIDER_CONNECTION_FAILED') from None
                except (ValueError, AttributeError):
                    raise DeliveryError('PROVIDER_RESPONSE_INVALID') from None
                sent += 1
            except Exception:
                if not self.fail_silently:
                    raise
        return sent
