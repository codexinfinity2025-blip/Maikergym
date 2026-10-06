# MaikerGym - Guía Rápida de Inicio

## ¿Qué se ha hecho?

Se ha integrado **Django** al proyecto MaikerGym para:
- ✅ Gestión de base de datos exclusivamente con MySQL
- ✅ Autenticación de usuarios con roles (Admin, Moderador, Usuario)
- ✅ Panel administrativo para gestión de perfiles
- ✅ Protección de vistas según rol del usuario
- ✅ Migraciones y estructura Django configurada

## Estructura del Proyecto

```
gym_project/
├── manage.py                      # Gestor Django
├── setup.py                       # Script de inicialización
├── requirements.txt               # Dependencias
├── README_DJANGO.md               # Documentación completa
│
├── gym_project/                   # Proyecto Django
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   
│   └── gym_app/                   # App principal
│       ├── models.py              # Modelo PerfilUsuario
│       ├── views.py               # Vistas protegidas
│       ├── urls.py                # Rutas
│       ├── admin.py               # Admin panel
│       ├── signals.py             # Señales de Django
│       │
│       ├── templates/             # Plantillas HTML
│       │   ├── base.html
│       │   ├── inicio.html
│       │   ├── login.html
│       │   ├── cuenta.html
│       │   ├── panel_moderador.html
│       │   └── panel_admin.html
│       │
│       └── static/                # Archivos estáticos
│           ├── css/
│           └── js/
```

## Inicio Rápido

### 1. Configura MySQL y arranca el servidor

Configura las variables `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`,
`MYSQL_HOST` y `MYSQL_PORT` en `.env` (consulta `.env.example`). Inicia MySQL y ejecuta:

```powershell
python create_mysql_db.py
python manage.py migrate
python manage.py runserver
```

El servidor estará disponible en `http://127.0.0.1:8000/`.

### 2. Cuentas locales de desarrollo

El archivo `setup.py` puede crear cuentas locales para realizar pruebas.

Las contraseñas se configuran mediante las variables
`TEST_ADMIN_PASSWORD`, `TEST_MODERATOR_PASSWORD` y
`TEST_USER_PASSWORD` dentro del archivo privado `.env`.

Las contraseñas no deben documentarse ni subirse a GitHub.

### 3. Accede a las siguientes URLs

- **Inicio**: `http://127.0.0.1:8000/`
- **Login**: `http://127.0.0.1:8000/login/`
- **Panel Admin** (solo admin): `http://127.0.0.1:8000/panel-admin/`
- **Panel Moderador** (admin/mod): `http://127.0.0.1:8000/panel-moderador/`
- **Mi Cuenta** (autenticado): `http://127.0.0.1:8000/cuenta/`
- **Admin Panel**: `http://127.0.0.1:8000/admin/` (con credenciales de superuser)

## Base de Datos

### Modelo PerfilUsuario

```python
PerfilUsuario
├── user (OneToOne → User de Django)
├── rol (admin, moderador, usuario)
├── objetivo (estetico, hipertrofia, salud, nutricion, recuperar)
├── fecha_registro (automático)
└── activo (booleano, default=True)
```

## Comandos Útiles

```bash
# Iniciar servidor
python manage.py runserver

# Crear superusuario (admin de Django)
python manage.py createsuperuser

# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Acceder a la shell interactiva de Django
python manage.py shell

# Ver usuarios existentes
python manage.py shell
>>> from django.contrib.auth.models import User
>>> User.objects.all()

# Crear nuevo usuario por terminal
python manage.py createsuperuser
```

## Próximos Pasos Recomendados

1. **Copiar archivos CSS/JS estáticos**:
   - Copiar archivos CSS de la carpeta raíz a `gym_project/gym_app/static/css/`
   - Esto permite que los templates tengan acceso a los estilos

2. **Agregar más modelos**:
   - `Rutina` (ejercicios para cada objetivo)
   - `Plan` (planes de precios)
   - `Alimento` (para nutrición)
   - `Comentario` (sistema de mensajería)

3. **Mejorar vistas**:
   - Agregar funcionalidad a los botones del panel admin/moderador
   - Implementar formularios para CRUD de datos
   - Agregar búsqueda y filtros

4. **Seguridad**:
   - Cambiar `SECRET_KEY` en production
   - Usar una cuenta MySQL con permisos limitados en producción
   - Configurar HTTPS

5. **API REST** (Opcional):
   - Instalar `django-rest-framework`
   - Crear endpoints para móvil/frontend externo

## Detención del Servidor

Para detener el servidor, en la terminal PowerShell presiona: `CTRL + C`

## Problemas Comunes

**Q: ¿Cómo cambio la contraseña de un usuario?**
```bash
python manage.py shell
>>> from django.contrib.auth.models import User
>>> u = User.objects.get(email='admin@maiker.test')
>>> u.set_password('nueva_contraseña')
>>> u.save()
```

**Q: ¿Cómo accedo al admin de Django?**
- Necesitas crear un superusuario con `python manage.py createsuperuser`
- Luego accede a `http://127.0.0.1:8000/admin/`

**Q: ¿Cómo agrego estilos CSS?**
- Coloca los archivos CSS en `gym_project/gym_app/static/css/`
- Usa en templates: `<link rel="stylesheet" href="{% static 'css/nombre.css' %}">`

---

**¡Proyecto listo para usar con Django! 🚀**
