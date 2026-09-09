import logging
from urllib.parse import urlsplit
from django.conf import settings
from django.contrib.auth import views as auth_views
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from .security import limitar_acceso
from .email_delivery import configuration_errors, DeliveryError


@method_decorator(never_cache, name='dispatch')
@method_decorator(limitar_acceso, name='dispatch')
class RecuperarPassword(auth_views.PasswordResetView):
    template_name = 'recuperar_password.html'
    email_template_name = 'emails/recuperar_password.txt'
    subject_template_name = 'emails/recuperar_password_asunto.txt'
    success_url = reverse_lazy('password_reset_done')

    def form_valid(self, form):
        origen = urlsplit(settings.PUBLIC_BASE_URL)
        errores = configuration_errors()
        if errores:
            logging.getLogger(__name__).error('PASSWORD_RESET_CONFIG: %s', ', '.join(errores))
            return self.render_to_response(self.get_context_data(form=form, servicio_no_disponible=True), status=503)
        try:
            form.save(request=self.request, use_https=origen.scheme == 'https',
                domain_override=origen.netloc, from_email=settings.DEFAULT_FROM_EMAIL,
                email_template_name=self.email_template_name,
                subject_template_name=self.subject_template_name)
        except Exception as error:
            # No registrar direcciones, credenciales, tokens ni respuestas del proveedor.
            codigo = str(error) if isinstance(error, DeliveryError) else type(error).__name__
            logging.getLogger(__name__).error('PASSWORD_RESET_DELIVERY_FAILED: %s', codigo)
            # Same public response for known/unknown accounts prevents enumeration.
        from django.http import HttpResponseRedirect
        return HttpResponseRedirect(self.success_url)


@method_decorator(never_cache, name='dispatch')
class ConfirmarPassword(auth_views.PasswordResetConfirmView):
    template_name = 'confirmar_password.html'
    success_url = reverse_lazy('password_reset_complete')
    post_reset_login = False

    def dispatch(self, *args, **kwargs):
        respuesta = super().dispatch(*args, **kwargs)
        respuesta['Referrer-Policy'] = 'no-referrer'
        return respuesta
