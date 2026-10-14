# Auditoría funcional de MaikerGym

Fecha: 14 de octubre de 2026. Repositorio revisado: `C:/Users/ogait/OneDrive/Desktop/MaikerGymPrime/gym`. Base de Git: `c3445da`; las correcciones de esta auditoría quedan locales, sin commit ni despliegue.

## Resultado

La suite final ejecutó **114 pruebas en 126.274 segundos: OK**. El núcleo funcional comprobado pasa las pruebas. Esto no certifica que toda función anunciada esté terminada ni que producción esté usando estas correcciones.

## Entorno y aislamiento

El entorno inicial usaba Python 3.14.7, Django 4.2.11 y MariaDB 10.4.32 local. La ejecución inicial tuvo 2 fallos y 32 errores, principalmente por incompatibilidad entre Django antiguo y Python 3.14. Al instalar las dependencias fijadas, Django 5.2.17 rechazó MariaDB 10.4.32.

Se creó un entorno virtual separado con `requirements.txt` y una instancia temporal MariaDB 10.11.16, usando `django.db.backends.mysql`, limitada a 127.0.0.1:3314. El paquete fue descargado del proveedor y su SHA-256 coincidió con la suma publicada. Las pruebas crearon y destruyeron bases separadas. La revisión de navegador usó una base de auditoría nueva y un usuario sintético. No se modificó el `.env`, no se migró la base existente y no se modificaron cuentas de producción.

La primera suite en el entorno compatible ejecutó 103 pruebas: 102 aprobadas y 1 error de una prueba desactualizada. La verificación final incluye 11 pruebas nuevas. La ejecución se hizo sobre MariaDB compatible; no reproduce exactamente Python 3.12/Gunicorn/MySQL del contenedor de Railway.

Compatibilidad de base de datos: [documentación oficial Django 5.2](https://docs.djangoproject.com/en/5.2/ref/databases/). El entorno local existente todavía necesita un servidor compatible y usar las dependencias fijadas; no se actualizó su instalación de XAMPP/MariaDB.

## Fallos reproducidos y corregidos

| Hallazgo | Corrección | Evidencia |
| --- | --- | --- |
| El servidor aceptaba nombre o apellido vacíos aunque el HTML los exigía | Validación de ambos campos en el servidor | Prueba con valores vacíos/espacios |
| Campos demasiado largos podían causar error de MySQL | Límites de nombres, correo usado como username, documento, teléfono y dirección, tomados de los modelos | Casos de longitudes inválidas sin creación de usuario |
| Un fallo al guardar el perfil dejaba creado el usuario | Creación de usuario y perfil dentro de una transacción; manejo de IntegrityError y conservación de la elección de plan hasta completar el guardado | Fallo simulado del perfil con comprobación de rollback |
| Una colisión durante la creación podía terminar en HTTP 500 | Mensaje de registro recuperable ante conflicto de integridad | Colisión simulada de create_user |
| Datos personales aceptaba un género fuera del catálogo | Validación con GeneroChoice antes de guardar | POST inválido devuelve 400 y no completa el perfil |
| Pesos NaN/sNaN provocaban decimal.InvalidOperation | Rechazo de decimales no finitos con ValidationError | NaN, sNaN e infinitos |
| Una prueba esperaba validar cantidad_dias, campo retirado del formulario | Prueba ajustada para comprobar que mandan los días seleccionados y que se ignora el campo histórico | Selección sábado/domingo conservada |

Se documentó también en `README_DJANGO.md` la compatibilidad mínima del servidor y el uso de un entorno virtual.

## Cobertura funcional comprobada

- Pruebas existentes de registro, edad, medidas, fotos, autenticación, CSRF, roles, recuperación de contraseña y proveedores de correo simulados.
- Generación automática, cobertura de movimientos, objetivos, niveles, disponibilidad, preferencias y conservación de rutinas manuales e historial.
- Calendarios, fin de semana, reposición de días y rachas.
- Grupos, límites, permisos, propuestas, calendario social y protección contra duplicación de puntos.
- Eliminación de cuentas, transferencia de administración y conservación de planes compartidos.
- Nuevos recorridos completos por series para repeticiones, tiempo y distancia: orden, descanso, omisión de descanso, resultados acumulados, sesión completada y puntos entregados una sola vez.
- Rechazo de series/sesiones pertenecientes a otra cuenta.
- Eliminación de cuenta con sesión grupal completada, recompensas y último integrante del grupo.
- GET de 13 páginas públicas y 10 autenticadas; comprobación de denegación de acceso de usuario común a paneles.

La cobertura no incluye una prueba de carga ni todas las condiciones de concurrencia.

## Navegador y archivos

Se verificó en navegador local el login, selección de fin de semana, cambio de unidades de descanso (1 minuto a 60 segundos), recuperación de minutos por día (75/90), generación automática para el miércoles, navegación desde nutrición y apertura del entrenamiento. Se inició y finalizó una serie: el panel mostró 1 de 12 series, 8% y el descanso de 120 segundos. El visor cargó la animación de sentadilla goblet; no registró errores de consola en los puntos inspeccionados.

La revisión adaptable comprobó disposición en una columna y ausencia de desbordamiento horizontal en la observación de un viewport efectivo de 480 px. No es una revisión de todos los teléfonos ni de todos los ejercicios 3D, avatares o movimientos. Hubo tiempos de espera de la herramienta de navegador; se inspeccionó el estado posterior antes de continuar.

La sospecha inicial de que faltaba el JSON `tiempos-guardados` fue descartada: el elemento existe y sus interacciones funcionaron. No se cambió ese formulario.

- 89 referencias estáticas literales en plantillas: sin archivos faltantes.
- `collectstatic` con ajustes de build y carpeta temporal: OK.
- Sintaxis de `reproductor_entrenamiento.js`, `rutina-editor.js`, `maikergym-motion.js` y `mensajes-diarios.js` con `node --check`: OK.
- `manage.py check`: sin problemas.
- `makemigrations --check --dry-run`: sin cambios de esquema.
- `git diff --check`: sin errores de espacios; Git avisa sobre conversión LF/CRLF en Windows.

## Producción: verificación limitada

Solicitudes GET al sitio Railway devolvieron 200 en `/health/`, `/`, `/login/`, `/registrarse/` y `/static/entrenador3d/entrenador.html`. No se obtuvo el commit del despliegue activo ni se reprodujo el borrado sobre una cuenta de producción. Las correcciones de esta auditoría todavía no están publicadas.

## Funciones y verificaciones pendientes

1. **Eliminación en Railway:** las pruebas locales pasan, incluyendo relaciones sociales protegidas; queda verificar el despliegue activo y el traceback del caso documentado en el empalme.
2. **Correo real:** las pruebas simulan Resend/Gmail. No se envió correo externo ni se certificó entrega con las credenciales de producción.
3. **Paneles personalizados:** botones sin operación y contenido de ejemplo en administrador/moderador. Django Admin es el módulo operativo existente. Completar estos paneles requiere implementar sus funciones, no simplemente corregir un fallo.
4. **Membresías:** la selección de precio guarda una preferencia; no hay cobro ni control de vencimiento.
5. **3D:** revisión visual de una demostración; faltan pruebas sistemáticas de todos los ejercicios, ambos modelos, rendimiento y exactitud técnica.
6. **Operación:** no se verificó restauración de respaldos, persistencia real del volumen de media ni comportamiento bajo carga.

## Archivos cambiados

- `gym_project/gym_app/views.py`: registro transaccional y validación de entrada.
- `gym_project/gym_app/services.py`: validación de pesos no finitos.
- `gym_project/gym_app/test_functional_audit.py`: 11 pruebas nuevas.
- `gym_project/gym_app/test_flexible_schedule.py`: actualización de la prueba del formulario actual.
- `README_DJANGO.md`: compatibilidad del entorno local.

Las evidencias adjuntas incluyen el log final de pruebas y capturas del reproductor. El código queda listo para revisión; no se realizó push ni despliegue.
