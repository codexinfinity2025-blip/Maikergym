from functools import wraps
from hashlib import sha256
from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
from .models import LimiteAcceso


def limitar_acceso(vista):
    @wraps(vista)
    def protegida(request, *args, **kwargs):
        if request.method == 'POST':
            identificador = str(request.user.pk) if request.user.is_authenticated else request.POST.get('email', '').strip().lower()[:254]
            ventana = int(timezone.now().timestamp()) // 900
            clave = sha256(f'{vista.__name__}:{identificador}:{ventana}'.encode()).hexdigest()
            with transaction.atomic():
                LimiteAcceso.objects.get_or_create(clave=clave, defaults={'ventana': ventana})
                limite = LimiteAcceso.objects.select_for_update().get(clave=clave)
                if limite.intentos >= 10:
                    respuesta = HttpResponse('Demasiados intentos. Espera hasta 15 minutos antes de volver a intentarlo.', status=429)
                    respuesta['Retry-After'] = '900'
                    return respuesta
                limite.intentos += 1
                limite.save(update_fields=['intentos'])
                LimiteAcceso.objects.filter(ventana__lt=ventana - 4).delete()
        return vista(request, *args, **kwargs)
    return protegida
