"""Entrega restringida de archivos; nunca publicar HTML subido al servidor."""
from pathlib import Path
from django.conf import settings
from django.core.exceptions import SuspiciousFileOperation, ValidationError
from django.core.files import File
from django.http import FileResponse, Http404
from django.utils._os import safe_join
from django.views.static import serve
from .profile_validation import normalizar_foto


def media_segura(request, path):
    try:
        archivo = Path(safe_join(settings.MEDIA_ROOT, path)).resolve()
        archivo.relative_to(Path(settings.MEDIA_ROOT).resolve())
    except (SuspiciousFileOperation, ValueError):
        raise Http404
    if not archivo.is_file():
        raise Http404
    if path.startswith('perfiles/'):
        # También protege fotos antiguas, sin borrar archivos del usuario.
        try:
            with archivo.open('rb') as origen:
                foto = normalizar_foto(File(origen))
        except (ValidationError, OSError):
            raise Http404
        response = FileResponse(foto, content_type='image/jpeg')
        response['Cache-Control'] = 'private, max-age=3600'
    else:
        if archivo.suffix.lower() not in {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.glb', '.gltf', '.bin'}:
            raise Http404
        response = serve(request, path, document_root=settings.MEDIA_ROOT)
    response['X-Content-Type-Options'] = 'nosniff'
    return response
