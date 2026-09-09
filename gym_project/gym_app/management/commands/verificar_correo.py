from django.core.management.base import BaseCommand, CommandError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from gym_project.gym_app.email_delivery import configuration_errors, DeliveryError


class Command(BaseCommand):
    help = 'Comprueba configuración sin mostrar secretos. --destinatario envía un correo de prueba sin tokens.'

    def add_arguments(self, parser):
        parser.add_argument('--destinatario')

    def handle(self, *args, **options):
        errors = configuration_errors()
        if errors:
            raise CommandError(', '.join(errors))
        self.stdout.write('Configuración presente. Esto no confirma conectividad ni entrega.')
        recipient = options.get('destinatario')
        if not recipient:
            return
        try:
            validate_email(recipient)
        except ValidationError:
            raise CommandError('DESTINATARIO_INVALIDO') from None
        try:
            count = send_mail('MaikerGym · prueba de correo',
                'Prueba de configuración. No contiene contraseñas ni enlaces de recuperación.',
                None, [recipient], fail_silently=False)
        except Exception as error:
            code = str(error) if isinstance(error, DeliveryError) else type(error).__name__
            raise CommandError('ENVIO_FALLIDO: ' + code) from None
        if count != 1:
            raise CommandError('PROVEEDOR_NO_ACEPTO_MENSAJE')
        self.stdout.write('Proveedor aceptó el mensaje. Confirma recepción en bandeja de entrada o spam.')
