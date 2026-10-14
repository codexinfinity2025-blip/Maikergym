"""Validación compartida de medidas y fotos, también fuera del formulario."""
from io import BytesIO
from uuid import uuid4
from datetime import date
from math import isfinite, log10
import warnings

from django import forms
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError
from django.utils import timezone


EDAD_MINIMA = 14

# Valores nominales de las siluetas: son una autoestimación visual adulta,
# no una medición ni un umbral de salud.
REFERENCIAS_GRASA_VISUAL = {
    'masculino': (8, 12, 15, 20, 25, 30, 35),
    'femenino': (15, 20, 25, 30, 35, 40, 45),
}


def validar_fecha_nacimiento(valor, hoy=None):
    """Validate age on the server using birthdays, not elapsed day counts."""
    hoy = hoy or timezone.localdate()
    try:
        nacimiento = valor if isinstance(valor, date) else date.fromisoformat(valor)
    except (ValueError, TypeError):
        raise ValidationError('Ingresa una fecha de nacimiento válida.')
    if nacimiento > hoy:
        raise ValidationError('La fecha de nacimiento no puede estar en el futuro.')
    edad = hoy.year - nacimiento.year - ((hoy.month, hoy.day) < (nacimiento.month, nacimiento.day))
    if edad < EDAD_MINIMA:
        raise ValidationError('MaikerGym está disponible desde los 14 años.')
    return nacimiento


def validar_medida(valor, nombre):
    minimo, maximo = (50, 250) if nombre == 'altura_cm' else (1, 500)
    try:
        return forms.DecimalField(min_value=minimo, max_value=maximo,
                                  max_digits=5, decimal_places=2).clean(valor)
    except ValidationError:
        etiqueta = 'Altura (cm)' if nombre == 'altura_cm' else 'Peso (kg)'
        raise ValidationError(f'{etiqueta}: utiliza un número entre {minimo} y {maximo}, con máximo dos decimales.')


def estimar_grasa_navy(genero, altura_cm, abdomen_cm, cuello_cm, cadera_cm=None):
    """Estimación adulta por circunferencias U.S. Navy/Hodgdon–Beckett.

    Los coeficientes de densidad reciben las medidas en centímetros. El valor
    es poblacional y aproximado, no una medición clínica individual.
    """
    try:
        altura, abdomen, cuello = map(float, (altura_cm, abdomen_cm, cuello_cm))
        cadera = float(cadera_cm) if cadera_cm is not None else None
    except (TypeError, ValueError):
        raise ValidationError('Ingresa medidas numéricas válidas en centímetros.')

    valores = (altura, abdomen, cuello) + ((cadera,) if cadera is not None else ())
    if not all(isfinite(valor) for valor in valores):
        raise ValidationError('Ingresa medidas numéricas válidas en centímetros.')
    if not 50 <= altura <= 250 or not 40 <= abdomen <= 200 or not 20 <= cuello <= 80:
        raise ValidationError('Revisa altura, abdomen y cuello; alguna medida está fuera del rango permitido.')

    if genero == 'masculino':
        diferencia = abdomen - cuello
        if diferencia <= 0:
            raise ValidationError('La medida del abdomen debe ser mayor que la del cuello.')
        densidad = 1.0324 - 0.19077 * log10(diferencia) + 0.15456 * log10(altura)
    elif genero == 'femenino':
        if cadera is None or not 50 <= cadera <= 220:
            raise ValidationError('Ingresa la medida de cadera entre 50 y 220 cm.')
        diferencia = abdomen + cadera - cuello
        if diferencia <= 0:
            raise ValidationError('Revisa las medidas de abdomen, cadera y cuello.')
        densidad = 1.29579 - 0.35004 * log10(diferencia) + 0.22100 * log10(altura)
    else:
        raise ValidationError('Esta ecuación requiere la referencia masculina o femenina correspondiente.')

    porcentaje = 495 / densidad - 450
    if not isfinite(porcentaje) or not 2 <= porcentaje <= 60:
        raise ValidationError('El cálculo no es válido para esas medidas; revísalas o continúa sin estimar.')
    return round(porcentaje, 1)


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
