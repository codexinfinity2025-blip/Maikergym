FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

COPY . .

# Incluye el visor, Three.js y los avatares GLTF como archivos estáticos.
RUN python manage.py collectstatic --noinput --settings=gym_project.build_settings

CMD ["/bin/sh", "-c", "python manage.py migrate --noinput && exec gunicorn gym_project.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --threads 2 --timeout 180 --access-logfile - --error-logfile -"]
