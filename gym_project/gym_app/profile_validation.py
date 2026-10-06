"""Validación compartida de medidas y fotos, también fuera del formulario."""
from io import BytesIO
from uuid import uuid4
import warnings

from django import forms
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError


def validar_medida(valor, nombre):
    minimo, maximo = (50, 250) if nombre == 'altura_cm' else (1, 500)
    try:
        return forms.DecimalField(min_value=minimo, max_value=maximo,
                                  max_digits=5, decimal_places=2).clean(valor)
    except ValidationError:
        etiqueta = 'Altura (cm)' if nombre == 'altura_cm' else 'Peso (kg)'
        raise ValidationError(f'{etiqueta}: utiliza un número entre {minimo} y {maximo}, con máximo dos decimales.')


def normalizar_foto(archivo):
    """No confiar en extensión/MIME. Reescribir los píxeles elimina metadatos y HTML."""
    if archivo.size > 5 * 1024 * 1024:
        raise ValidationError('La foto debe pesar como máximo 5 MB.')
    try:
        archivo.seek(0)
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(archivo) as imagen:
                if imagen.format not in {'JPEG', 'PNG', 'WEBP'} or imagen.width * imagen.height > 16_000_000:
                    raise ValidationError('Utiliza una foto JPG, PNG o WebP de máximo 16 megapíxeles.')
                imagen.verify()
            archivo.seek(0)
            with Image.open(archivo) as imagen:
                imagen = ImageOps.exif_transpose(imagen)
                imagen.thumbnail((1024, 1024))
                salida = BytesIO()
                imagen.convert('RGB').save(salida, format='JPEG', quality=85)
        return ContentFile(salida.getvalue(), name=f'{uuid4().hex}.jpg')
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError,
            Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ValidationError('La foto no es válida. Selecciona una imagen JPG, PNG o WebP.')
