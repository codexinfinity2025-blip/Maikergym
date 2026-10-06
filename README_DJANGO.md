# MaikerGym - Proyecto Django

Sistema de gestión para gimnasio con roles de usuario (Admin, Moderador, Usuario).

## Requisitos Previos

- Python 3.12 recomendado (Docker), Django 5.2 LTS.
- pip (gestor de paquetes de Python)

## Instalación y Configuración

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Realizar migraciones de base de datos

```bash
python manage.py migrate
```

### 3. Crear superusuario (Administrador de Django)

```bash
python manage.py createsuperuser
```

Sigue las instrucciones para crear una cuenta de administrador.

### 4. Crear usuarios de prueba

```bash
python setup.py
```

Las cuentas de desarrollo se crean mediante `setup.py`.

Sus contraseñas se configuran únicamente en el archivo local `.env`
y nunca deben incluirse en la documentación ni en el repositorio.

## Ejecutar el servidor

Antes de lanzar el servidor, asegúrate de tener Python instalado y el entorno preparado:

1. Instala dependencias:

```bash
pip install -r requirements.txt
```

2. Genera migraciones y aplica los cambios a la base de datos:

```bash
python manage.py migrate
```

3. Configura MySQL en `.env` con los datos de tu servidor local. Un ejemplo válido:

```env
MYSQL_DATABASE=fitness_db
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
```

4. Inicia el servidor local:

```bash
python manage.py runserver
```

El servidor estará disponible en: `http://127.0.0.1:8000/`

### Opción rápida para Windows

Ejecuta el archivo `run_local_windows.bat` desde la carpeta del proyecto para:
- crear `.env` desde `.env.example` si no existe
- instalar dependencias
- aplicar migraciones
- ejecutar el servidor

> Si no tienes Python en el PATH, instala Python 3.12 desde https://www.python.org/downloads/ y marca la opción "Add Python to PATH".

## Estructura del Proyecto

```
gym_project/
├── manage.py                      # Script de gestión de Django
├── setup.py                       # Script de inicialización
├── requirements.txt               # Dependencias del proyecto
│
├── gym_project/
│   ├── __init__.py
│   ├── settings.py               # Configuración de Django
│   ├── urls.py                   # URLs del proyecto
│   ├── wsgi.py                   # Configuración WSGI
│   │
│   └── gym_app/
│       ├── migrations/           # Migraciones de BD
│       ├── templates/            # Plantillas HTML
│       │   ├── base.html
│       │   ├── inicio.html
│       │   ├── login.html
│       │   ├── cuenta.html
│       │   ├── panel_moderador.html
│       │   └── panel_admin.html
│       ├── static/               # Archivos estáticos
│       │   ├── css/
│       │   └── js/
│       ├── __init__.py
│       ├── admin.py              # Configuración del admin
│       ├── apps.py               # Configuración de la app
│       ├── models.py             # Modelos de base de datos
│       ├── views.py              # Vistas
│       ├── urls.py               # URLs de la app
│       └── signals.py            # Señales de Django
```

## Funcionalidades

### Autenticación y Roles

- **Usuario**: Puede acceder a su cuenta y seleccionar objetivo de entrenamiento
- **Moderador**: Acceso a panel de moderación (revisión de usuarios y contenido)
- **Admin**: Acceso a panel administrativo (gestión completa del sistema)

### Base de Datos

Este proyecto usa MySQL configurado con `PyMySQL` en `gym_project/settings.py`. Ajusta los valores de conexión en `.env` para tu servidor local antes de ejecutar el proyecto.

### Configuración MySQL recomendada

1. Instala MySQL Server.
2. Crea la base de datos:

```sql
CREATE DATABASE maikergym CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
```

3. Crea un usuario y asigna permisos:

```sql
CREATE USER 'gymuser'@'localhost' IDENTIFIED BY 'tu_contraseña';
GRANT ALL PRIVILEGES ON maikergym.* TO 'gymuser'@'localhost';
FLUSH PRIVILEGES;
```

4. Configura los valores en `settings.py` o en un archivo `.env`.

### Vistas Protegidas

- `/` - Página de inicio
- `/login/` - Inicio de sesión
- `/logout/` - Cierre de sesión
- `/cuenta/` - Perfil de usuario (requiere autenticación)
- `/panel-moderador/` - Panel moderador (solo moderadores y admins)
- `/panel-admin/` - Panel admin (solo admins)

## Panel de Administración

Accede al panel administrativo en: `http://127.0.0.1:8000/admin/`

Con las credenciales del superusuario creado.

## Seguridad y despliegue

- MySQL es obligatorio en desarrollo, pruebas y producción. Configurar
  `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_HOST` y `MYSQL_PORT`.
  En producción (`DEBUG=False`) también se exige `SECRET_KEY` propia.
- `/health/` ejecuta `SELECT 1` y devuelve 503 si la base no está disponible.
- El contenedor aplica migraciones, pero no vuelve a cargar ni sobrescribir
  ejercicios/planes y tampoco crea administradores automáticamente.
- Solo al preparar una base nueva y vacía, ejecutar una vez:

```bash
python manage.py migrate --noinput
python manage.py inicializar_catalogo
python manage.py createsuperuser
```

El catálogo inicial contiene 42 ejercicios y 4 planes. `inicializar_catalogo`
rechaza bases con catálogo existente. Los antiguos comandos `cargar_ejercicios`
y `cargar_plan_hipertrofia` actualizan registros: no ejecutarlos en cada arranque.
Antes de actualizar una instalación existente, respaldar MySQL y el volumen de
archivos. Aplicar migraciones, sin volver a inicializar el catálogo.

Las fotos aceptan JPG/PNG/WebP de hasta 5 MB y 16 megapíxeles, se reducen a
1024 píxeles y se convierten a JPEG sin metadatos. La entrega de fotos antiguas
también rechaza contenido activo, sin borrar archivos. Peso: 1–500 kg;
altura: 50–250 cm; hasta dos decimales.

Desactivar el usuario o su perfil bloquea el acceso. Los cambios hechos con
`save()` se sincronizan entre ambos campos; el backend también bloquea estados
antiguos inconsistentes. Esta actualización cambia el backend de autenticación:
las sesiones anteriores deberán iniciar sesión nuevamente.

Verificación local (usa una base de pruebas, no la base de usuarios):

El usuario MySQL de desarrollo necesita permiso para crear y eliminar la base
`test_<MYSQL_DATABASE>`. Ejecutar las pruebas en un servidor local aislado, nunca
con las credenciales de producción. Django crea y elimina esa base de pruebas;
el motor utilizado es MySQL también durante los tests.

```bash
python manage.py test --noinput
python manage.py makemigrations --check --dry-run
```

El envío real de correo requiere credenciales del entorno y una prueba de
entrega; las pruebas simuladas no certifican que Gmail/Railway esté configurado.

## Funciones implementadas y pendientes

Ya existen rutinas, planes, orientación nutricional, grupos y seguimiento.
La preferencia mensual/semestral/anual no constituye una pasarela de pago ni
controla vencimientos. Los paneles personalizados aún tienen acciones pendientes;
la administración operativa se realiza desde `/admin/`.

Mejoras futuras:

- Implementar sistema de mensajería
- Agregar autenticación con redes sociales
- Crear API REST con Django REST Framework
- Mejorar interfaz de usuario con Bootstrap/Tailwind

## Licencia

© 2026 MaikerGym. Todos los derechos reservados.
