from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.views.static import serve


def health_check(request):
    """Respuesta liviana usada para comprobar el servicio publicado."""
    return JsonResponse({'status': 'ok', 'application': 'MaikerGym'})

urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('admin/', admin.site.urls),
    path('', include('gym_project.gym_app.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # En Railway la aplicación no tiene Nginx externo. El volumen conserva las
    # fotos de perfil y esta ruta las entrega sin exponer el directorio completo.
    urlpatterns += [
        path('media/<path:path>', serve, {'document_root': settings.MEDIA_ROOT}),
    ]
