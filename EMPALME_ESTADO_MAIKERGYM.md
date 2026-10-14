# Empalme del estado actual — MaikerGym

**Corte de información:** 14 de octubre de 2026.
**Alcance:** lo que existe en el repositorio web MaikerGym y su estado comprobable a esta fecha. Este documento registra activos, funcionalidades, ubicación y estado de Git/despliegue; no es una lista de tareas futuras.

## Identificación y ubicación

- **Carpeta local del repositorio:** `C:\Users\ogait\OneDrive\Desktop\MaikerGymPrime\gym`
- **Git root:** esa misma carpeta; contiene `.git`, `manage.py`, `Dockerfile` y `railway.json`.
- **Aplicación:** Django, nombre/proyecto Python `gym_project`, aplicación principal `gym_project.gym_app`.
- **Sitio público:** <https://maikergym-production.up.railway.app/>
- **Dominio del servicio Railway mostrado en el panel:** `maikergym-production.up.railway.app`.

## Estado Git verificado

- **Rama local:** `main`.
- **Árbol de trabajo al revisar:** limpio.
- **HEAD local:** `87378365acfe6132df44a9263d8fe7080352ad67` (`8737836`).
- **GitHub de despliegue — remoto `nuevo`:** `https://github.com/codexinfinity2025-blip/Maikergym.git`, rama `main`.
- **Punta comprobada de `nuevo/main`:** `87378365acfe6132df44a9263d8fe7080352ad67`, igual al HEAD local. Esto confirma que el commit local más reciente está publicado en ese remoto.
- **Otro remoto — `origin`:** `https://github.com/ogaitnas08soft/maikergym-prime.git`. Es un repositorio distinto; la rama local aparecía cinco commits por delante de `origin/main`. El destino que se ha usado para publicar MaikerGym es `nuevo`, no `origin`.
- **Comando de publicación usado para ese remoto:** desde la carpeta del repositorio, `git push nuevo HEAD:main`.

### Últimos commits relevantes

| Commit | Mensaje | Contenido comprobado |
| --- | --- | --- |
| `8737836` | `Registrar errores inesperados al eliminar cuentas` | Registra con traceback en el logger las excepciones inesperadas del flujo de borrado y muestra mensaje de error en la cuenta. Está en `nuevo/main`. |
| `b23a1c4` | `Permitir borrar cuentas con rutinas protegidas` | Añade manejo para borrar una cuenta que tiene rutinas, sesiones y vínculos protegidos; incluye pruebas. |
| `ced3f27` | `Corregir eliminación segura de cuentas` | Confirma contraseña, prepara la salida de grupos y corrige el flujo de borrado con retorno a la página; incluye pruebas. |
| `1b70bf0` | `Mejorar registro y preparar despliegue Railway` | Formularios de registro/datos personales, documentos, validación de edad, guía visual corporal, configuración de descanso y documentación Railway. |
| `76e909a` | `Usar solo MySQL y corregir seguridad; 90 pruebas aprobadas` | Establece MySQL como base del proyecto y reúne cambios de seguridad. El número del mensaje es histórico; no representa una ejecución de toda la suite en este corte. |

## Qué contiene el proyecto

MaikerGym es una aplicación web Django para cuentas de gimnasio, personalización de rutinas, sesiones de entrenamiento, seguimiento, orientación de nutrición y funciones sociales. El backend usa MySQL; el frontend usa plantillas Django, CSS y JavaScript estáticos.

### Funcionalidades presentes en el código

- **Cuentas y acceso:** registro, inicio/cierre de sesión, recuperación y cambio de contraseña; roles de administrador, moderador y usuario; controles de acceso y limitación de intentos.
- **Registro y perfil:** nombre, apellido, correo, fecha de nacimiento, tipo/número de documento opcional, género, peso, altura, teléfono, dirección, foto, objetivo y preferencias. El catálogo de documentos incluye CC, CE, TI, RC, PPT, PA, SC, CD, LC, TP y LM. La validación de edad del servidor admite desde los 14 años.
- **Datos personales y composición corporal:** paso separado para terminar datos del perfil. Presenta de manera opcional una estimación por circunferencias U.S. Navy y una guía visual cualitativa; la página advierte que son referencias aproximadas y no aplica esa valoración a menores. La imagen está en `gym_project/gym_app/static/img/body-composition/guia_visual_usuario.png`.
- **Preferencias y creación de rutinas:** objetivo, nivel, prueba de nivel, enfoque corporal, días elegidos de la semana, minutos disponibles por día, descanso configurable en segundos o minutos y modalidad automática o personalizada. El formulario no pide un segundo género en el paso de días.
- **Rutinas automáticas y manuales:** catálogo de ejercicios y planes; planificación por objetivo/nivel/calendario; creación y edición de rutinas personales; reglas de cobertura y restricciones que devuelven error cuando no es posible generar una sesión válida. La documentación de fundamentos distingue claramente las reglas propias del producto de las recomendaciones generales de OMS/ACSM.
- **Entrenamiento:** asignaciones, horarios, sesiones, ejercicios y series; reproductor de sesión, estados de avance, temporizador/descanso y registro de actividad.
- **Nutrición y bienestar:** pantallas de orientación de nutrición y contenido de bienestar/mensajes diarios.
- **Funciones sociales:** grupos de amigos, integrantes, rutinas y participaciones grupales, avisos, días comprometidos, resultados y recompensas.
- **Cuenta:** edición del perfil, preferencias, foto y contraseña; existe acción de eliminación de cuenta con confirmación de contraseña y lógica de desvinculación/transferencia para datos de rutinas y grupos.
- **Paneles:** rutas y plantillas para administrador y moderador, además de Django Admin.
- **Visor/entrenador 3D incluido en el repositorio:** página y recursos Three.js/GLTF en `gym_project/gym_app/static/entrenador3d/`; incluye assets `.gltf`, `.glb`, texturas y copias locales de `three.module.js`, `GLTFLoader.js` y `OrbitControls.js`. Lo listado aquí describe exclusivamente esos assets versionados del sitio; no certifica ni representa como terminados otros archivos Blender o bibliotecas externas.

## Mapa de carpetas y archivos principales

```text
MaikerGymPrime/gym/
├── gym_project/
│   ├── settings.py                 Configuración Django/MySQL y entorno
│   ├── urls.py                     Rutas raíz, health check y media segura
│   ├── wsgi.py / asgi.py           Entradas WSGI/ASGI
│   ├── build_settings.py           Configuración de build/archivos estáticos
│   └── gym_app/
│       ├── models.py               Perfil, catálogo, planes, calendario y sesiones
│       ├── social_models.py         Grupos, participaciones, avisos y resultados
│       ├── views.py                Registro, cuenta, rutinas, entrenamientos y páginas
│       ├── social_views.py         Flujos sociales
│       ├── services.py             Generación y creación de rutinas
│       ├── routine_basis.py        Reglas de distribución semanal
│       ├── routine_edit.py         Edición/protección de sesiones y rutinas
│       ├── profile_validation.py   Edad, medidas y normalización de fotos
│       ├── registration_review.py  Revisión del registro
│       ├── profile_preferences.py  Preferencias de perfil
│       ├── password_reset.py       Recuperación/cambio por token
│       ├── auth_backend.py         Acceso condicionado al estado de perfil
│       ├── security.py             Límite de intentos/acceso
│       ├── email_delivery.py       Backends de correo
│       ├── migrations/             Esquema versionado; última migración 0021
│       ├── management/commands/    Catálogo inicial y verificación de correo
│       ├── templates/              HTML de páginas y parciales
│       ├── static/css/              Estilos
│       ├── static/js/               Interacciones y reproductor
│       ├── static/img/              Guías e imágenes del sitio
│       └── static/entrenador3d/     Visor y activos 3D
├── docs/                            Organización y fundamento de rutinas
├── backups/                         Carpeta local de respaldos
├── codex_backups/                   Carpeta de copias locales (ignorada por Git)
├── media/                            Archivos multimedia locales/usuarios
├── Dockerfile                       Imagen, dependencias y collectstatic
├── railway.json                     Health check/reinicio Railway
├── requirements.txt                 Dependencias Python fijadas
├── DESPLIEGUE_RAILWAY.md             Configuración documentada de Railway
├── README_DJANGO.md                  Guía de arquitectura/operación
├── INICIO_RAPIDO.md                  Inicio local en Windows
├── RECUPERACION_CORREO.md            Configuración de correo
├── manage.py                         Comandos Django
└── .env.example                      Nombres/formato de variables, sin secretos
```

La configuración privada `.env` existe localmente y está excluida de Git y de la imagen Docker. **No se incluye ni se copia ningún valor secreto en este empalme.** `media/`, `staticfiles/`, `backups/` y `codex_backups/` también se excluyen de la imagen; sus contenidos no deben suponerse parte del respaldo de GitHub.

## Datos y modelos principales

- **Perfil/cuenta:** `PerfilUsuario` relacionado uno-a-uno con el usuario de Django; guarda rol, fecha de nacimiento/edad, documento, género, medidas, foto, enfoque, días y preferencias de entrenamiento.
- **Catálogo y programación:** `Ejercicio`, `PlanEntrenamiento`, `FasePlan`, `DiaPlan`, `EjercicioProgramado`.
- **Seguimiento:** `AsignacionPlanUsuario`, `HorarioPlanUsuario`, `SesionEntrenamiento`, `EjercicioSesion`, `SerieEjercicioSesion`.
- **Seguridad:** `LimiteAcceso`.
- **Social:** `GrupoAmigos`, `IntegranteGrupo`, `RecompensaEjercicio`, `DiaComprometido`, `RutinaGrupal`, `ParticipacionGrupal`, `AvisoSocial`, `ResultadoGrupo`.
- **Esquema:** migraciones numeradas `0001`–`0021`; `0021_perfilusuario_documento_perfilusuario_tipo_documento.py` incorpora el tipo de documento al perfil.

## Rutas disponibles

La lista registrada en `gym_project/gym_app/urls.py` cubre `/`, `/escogenos/`, `/precios/`, `/registrarse/`, `/registro/revisar/`, `/datos-personales/`, `/login/`, `/logout/`, `/cuenta/`, `/cuenta/preferencias/`, `/cuenta/cambiar-contrasena/`, `/privacidad/`, `/objetivo/`, `/nivel/`, `/prueba-nivel/`, `/configurar-rutina/`, `/crear-rutina/`, `/rutinas/`, `/mi-entrenamiento/`, `/mi-entrenamiento/modificar/`, `/entrenamiento/sesion/<id>/`, `/dieta/`, `/nutricion/`, `/salud/`, `/hipertrofia/`, `/estetico/`, `/notificaciones/`, `/amigos/`, `/amigos/rutina/.../`, `/panel-moderador/` y `/panel-admin/`. En `gym_project/urls.py` están además `/health/`, `/admin/` y la ruta de entrega segura `/media/<path>`.

## Ejecución y despliegue que están configurados

- **Framework:** Django `5.2.17`; Python `3.12` en Docker.
- **Base de datos:** MySQL únicamente, con PyMySQL y variables de entorno `MYSQLDATABASE`, `MYSQLUSER`, `MYSQLPASSWORD`, `MYSQLHOST`, `MYSQLPORT` (los nombres locales históricos también se documentan en `.env.example`).
- **Arranque del contenedor:** instala `requirements.txt`, ejecuta `collectstatic`, después `migrate --noinput` y levanta Gunicorn en `$PORT` con access/error logs en stdout/stderr.
- **Estáticos:** WhiteNoise configurado para servir el build de estáticos.
- **Railway:** `railway.json` selecciona Dockerfile, health check `/health/`, timeout 300 s y reinicio `ON_FAILURE` hasta 10 reintentos.
- **Archivos subidos:** documentación indica montar volumen persistente en `/app/media` para fotos de perfil.
- **Health check:** `/health/` ejecuta `SELECT 1` contra MySQL; devuelve `status=ok` o `503` si la base no está disponible.
- **Correo:** están los backends Gmail y Resend y el comando `verificar_correo`; el envío real depende de variables/credenciales del proveedor configuradas fuera del repositorio.
- **Preparación catálogo nuevo:** `inicializar_catalogo` para una base vacía y `createsuperuser` para crear un administrador. El contenedor no crea catálogo ni administrador automáticamente.

## Estado conocido de eliminación de cuenta y Railway

- El flujo `/cuenta/` verifica la contraseña actual; contempla transferencia de administración de grupo si existe otro integrante, y la eliminación de un grupo vacío; elimina/desvincula objetos de la cuenta, sus asignaciones y referencias a sesiones antes de borrar el usuario. Si una rutina personal sigue asignada a otro usuario, se conserva desvinculada del propietario que sale.
- El commit `8737836` añade logging con `logger.exception` para capturar en el log de aplicación el traceback de excepciones inesperadas durante ese flujo y un mensaje de error seguro. Ese código ya está en `nuevo/main` según `git ls-remote`.
- **Evidencia de producción compartida en esta conversación:** captura del despliegue Railway `511dc31e`, marcado Active el 14-oct-2026 a las 15:24 GMT-5. Los logs aportados muestran que Gunicorn inició y las migraciones no tenían cambios pendientes. La petición `POST /cuenta/` de las 15:26:56 devolvió HTTP 500. El fragmento disponible solo contiene el access log de Gunicorn y no el traceback Django. No hay en este corte un log posterior que confirme qué despliegue está sirviendo el sitio tras el commit `8737836`.

## Verificación hecha para este empalme

- Se verificó el árbol limpio de Git, la rama `main`, el hash HEAD y el hash de `nuevo/main`.
- Después del cambio `8737836`, se ejecutó `python manage.py test gym_project.gym_app.tests.EliminacionCuentaTest --settings=gym_project.settings`: **4 pruebas, OK**.
- `git diff --check` pasó para ese cambio antes de confirmarlo.
- No se afirma aquí que se haya ejecutado la suite completa en este corte ni que se haya validado visualmente el sitio o la última entrega Railway después del hash registrado.

## Referencias internas del repositorio

- Despliegue y variables: `DESPLIEGUE_RAILWAY.md`.
- Arquitectura y operación: `README_DJANGO.md`.
- Arranque local Windows: `INICIO_RAPIDO.md` y `run_local_windows.bat`.
- Correo: `RECUPERACION_CORREO.md`.
- Organización: `docs/ORGANIZACION.md`.
- Criterios del generador: `docs/fundamento_rutinas.md`.
