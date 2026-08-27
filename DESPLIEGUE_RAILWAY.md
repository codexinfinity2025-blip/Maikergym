# Publicar MaikerGym en Railway

El proyecto está preparado para desplegarse en Railway con una aplicación
Django, una base de datos MySQL y un volumen persistente para las fotos de
perfil. No se utiliza GitHub Pages porque allí no puede ejecutarse Django ni
MySQL.

## Servicios necesarios

En un proyecto nuevo de Railway crea lo siguiente:

1. **MySQL**: usa la opción `Database` y elige `MySQL`.
2. **MaikerGym Web**: usa `Empty Project` y después despliega esta carpeta con
   la CLI de Railway.
3. **Volume**: agrégalo al servicio `MaikerGym Web` con ruta de montaje
   `/app/media`. Así las fotos de perfil sobreviven a cada actualización.

## Variables del servicio web

En `MaikerGym Web > Variables`, configura estas variables. Las primeras cinco
son referencias al servicio MySQL creado en el mismo proyecto.

```text
MYSQLDATABASE=${{MySQL.MYSQLDATABASE}}
MYSQLUSER=${{MySQL.MYSQLUSER}}
MYSQLPASSWORD=${{MySQL.MYSQLPASSWORD}}
MYSQLHOST=${{MySQL.MYSQLHOST}}
MYSQLPORT=${{MySQL.MYSQLPORT}}
DEBUG=False
SECRET_KEY=<valor aleatorio seguro generado por Railway>
DJANGO_SUPERUSER_USERNAME=admin_maikergym
DJANGO_SUPERUSER_EMAIL=admin@maikergym.local
DJANGO_SUPERUSER_PASSWORD=<contraseña nueva de al menos 12 caracteres>
```

No escribas contraseñas en este archivo, en Git o en el código. Railway las
guarda como secretos. La aplicación añade automáticamente el dominio público
de Railway a Django, por lo que no debes adivinarlo antes del despliegue.

## Qué se ejecuta al publicar

El `Dockerfile` aplica las migraciones, carga los 26 ejercicios, carga el plan
de hipertrofia de 12 semanas y crea el administrador si se han configurado las
tres variables `DJANGO_SUPERUSER_*`. Después inicia Gunicorn y Railway comprueba
la ruta `/health/` antes de dirigir visitantes a la aplicación.

## Verificación final

Cuando Railway entregue el dominio `https://...up.railway.app`, verifica:

1. `/health/` responde `{"status":"ok","application":"MaikerGym"}`.
2. `/admin/` permite ingresar con `admin_maikergym`.
3. Un usuario puede registrarse, iniciar sesión y abrir su entrenamiento.
4. El visor 3D carga sus archivos locales desde `/static/entrenador3d/`.
