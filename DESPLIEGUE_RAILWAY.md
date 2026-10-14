# Preparación y despliegue de MaikerGym en Railway

La aplicación se despliega como un servicio Django/Gunicorn con MySQL. El
`Dockerfile` ya instala dependencias, reúne los archivos estáticos con
WhiteNoise, ejecuta las migraciones pendientes al iniciar y arranca Gunicorn.
`.env` y los datos locales están excluidos tanto de Git como de la imagen Docker.

## Publicar GitHub y Railway con un comando en Windows

Las correcciones deben estar confirmadas en Git y la rama `main` debe estar limpia.
Desde PowerShell, en esta carpeta, ejecutar:

```powershell
.\PUBLICAR.cmd
```

El comando comprueba el remoto `nuevo` de
`codexinfinity2025-blip/Maikergym`, el acceso al proyecto vinculado de Railway,
sube `HEAD:main` y solicita un despliegue del servicio web existente. No crea
proyectos ni servicios nuevos. También existe el modo `--comprobar`, que no sube.

Requiere Git y la CLI oficial de Railway, disponible en PATH o en la copia
local ya usada por este proyecto. En otro equipo, instalar con
`npm install -g @railway/cli` e iniciar sesión con `railway login` en la cuenta
que tiene acceso al proyecto MaikerGym. El proyecto debe estar vinculado localmente.
En esta instalación se puede abrir el inicio de sesión con
`.\PUBLICAR.cmd --login`, que también encuentra la CLI local.

La vinculación antigua apuntaba a otro proyecto. El 14 de octubre de 2026 se
verificó el proyecto `sunny-charisma`, entorno `production`, servicio `Maikergym`,
con el dominio `maikergym-production.up.railway.app` y el repositorio correcto.
La cuenta `codexinfinity2025@gmail.com` tiene acceso. El script vuelve a vincular
explícitamente este destino antes del push. Los identificadores usados son:

- Proyecto: `a386113e-970d-4d54-907b-dbac9ea86d83`.
- Entorno: `7a3843e8-125f-4c89-a769-689a4af6fcfe`.
- Servicio web: `8571e71e-a8b8-4c3d-8866-fe4ecd5426ef`.

La salida exitosa significa que Railway aceptó la solicitud: aún debe terminar
el build y el health check. Si el servicio tiene autodeploy de GitHub habilitado,
el push también puede iniciar un despliegue; la subida explícita por CLI puede
generar otra entrega. Esta ruta no depende de que autodeploy esté habilitado.

## Servicios de Railway

En un proyecto de Railway crea:

1. Un servicio **MySQL**.
2. Un servicio web desde el repositorio GitHub de MaikerGym; el directorio raíz
   debe ser la carpeta que contiene este archivo y `Dockerfile`.
3. Un volumen en el servicio web, montado en `/app/media`, para conservar las
   fotos de perfil tras los despliegues.

Conecta el servicio web al repositorio y configura el despliegue para usar el
`Dockerfile` de la raíz. `railway.json` ya define la ruta de health check
`/health/` y el reinicio por fallo.

## Variables del servicio web

Configura las siguientes variables en **Variables**. Las referencias a MySQL
deben usar el nombre exacto del servicio de base de datos creado en Railway
(si se llama `MySQL`, estas expresiones funcionan):

```text
MYSQLDATABASE=${{MySQL.MYSQLDATABASE}}
MYSQLUSER=${{MySQL.MYSQLUSER}}
MYSQLPASSWORD=${{MySQL.MYSQLPASSWORD}}
MYSQLHOST=${{MySQL.MYSQLHOST}}
MYSQLPORT=${{MySQL.MYSQLPORT}}
DEBUG=False
SECRET_KEY=<secreto largo y aleatorio, exclusivo de producción>
```

Railway suministra `RAILWAY_PUBLIC_DOMAIN`; Django lo incorpora a los hosts
permitidos y al origen CSRF HTTPS automáticamente. No guardes claves ni
contraseñas en el repositorio, en `.env.example` ni en capturas compartidas.

### Correo

El correo transaccional no se configura solo. Para recuperación de contraseña,
configura un proveedor HTTPS con dominio remitente verificado, por ejemplo:

```text
EMAIL_BACKEND=gym_project.gym_app.email_delivery.ResendBackend
RESEND_API_KEY=<secreto del proveedor>
DEFAULT_FROM_EMAIL=<remitente verificado>
```

El backend SMTP está desactivado por defecto en Railway; no lo habilites salvo
que el plan y el proveedor permitan conexiones SMTP salientes. `PUBLIC_BASE_URL`
se puede omitir: la app la deriva del dominio de Railway. Si configuras correo,
valida la instalación con `python manage.py verificar_correo` y envía una prueba
solo a una dirección que controles.

## Primer arranque y datos iniciales

El contenedor ejecuta `python manage.py migrate --noinput` antes de Gunicorn;
esto incluye la migración 0021 de los campos de documento añadidos al registro.
Las migraciones no cargan automáticamente ejercicios, planes ni crean un
administrador. Cuando MySQL esté vacío, ejecuta una sola vez desde la consola
del servicio web:

```text
python manage.py inicializar_catalogo
python manage.py createsuperuser
```

`inicializar_catalogo` se detiene si ya existen ejercicios o planes, para no
reescribir catálogos de una base existente. Crea el administrador con
`createsuperuser`; no compartas ni guardes sus credenciales en este documento.

## Comprobación después del despliegue

Una vez que Railway asigne el dominio público:

1. `https://<dominio>/health/` debe responder `{"status":"ok","application":"MaikerGym"}`.
2. Abre `/registrarse/` y completa un registro de prueba.
3. Verifica login, configuración semanal, perfil y que las fotos sobrevivan a
   un redeploy gracias al volumen.
4. Si el correo quedó configurado, solicita un restablecimiento y confirma que
   llega el mensaje.
5. Revisa los registros del servicio web para confirmar que la migración
   0021 terminó sin error y que Gunicorn quedó escuchando.

No consideres la aplicación publicada/verificada hasta completar estas pruebas
en el dominio de Railway.
