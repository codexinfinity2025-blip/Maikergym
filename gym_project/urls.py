from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.db import connection, DatabaseError
from gym_project.gym_app.media_views import media_segura


def health_check(request):
    """Disponibilidad del servicio y de la base de datos, sin exponer secretos."""
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
    except DatabaseError:
        return JsonResponse({'status': 'unavailable', 'application': 'MaikerGym'}, status=503)
    return JsonResponse({'status': 'ok', 'application': 'MaikerGym'})

urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('admin/', admin.site.urls),
    path('media/<path:path>', media_segura, name='media_segura'),
    path('', include('gym_project.gym_app.urls')),
]
