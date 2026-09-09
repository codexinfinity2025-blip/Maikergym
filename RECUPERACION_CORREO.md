# Activar recuperación en Railway

## Gmail API por HTTPS (cuenta del gimnasio)

Backend disponible: `gym_project.gym_app.email_delivery.GmailBackend`.
Requiere `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET` y `GMAIL_REFRESH_TOKEN`
en las variables privadas del servicio. Mantener `DEFAULT_FROM_EMAIL` con
la cuenta autorizada y `PUBLIC_BASE_URL` con el origen público del aplicativo.
No activar el backend hasta obtener la autorización offline del remitente
con el permiso `https://www.googleapis.com/auth/gmail.send`.
El cliente de escritorio se usa únicamente en una herramienta local de
autorización; no convierte la web en una aplicación de escritorio.

En modo OAuth externo de prueba, Google limita a siete días la duración del
refresh token para este permiso. Antes de usarlo de forma permanente debe
revisarse el estado de publicación y los requisitos de verificación de Google.
No prometer envío permanente con un token de prueba. Nunca guardar credenciales
en el repositorio. El código no activa ni autoriza la cuenta por sí solo.

Fuentes: https://developers.google.com/workspace/gmail/api/guides/sending
y https://developers.google.com/identity/protocols/oauth2

## Importante: restricciones del alojamiento

Railway permite SMTP únicamente en Pro o superior. Trial/Free/Hobby requieren
un proveedor con API HTTPS. La contraseña de aplicación Gmail no elimina este bloqueo.
Fuente: https://docs.railway.com/networking/outbound-networking

## Opción HTTPS preparada (Resend)

Configurar solo después de elegir/autorizar el proveedor y verificar el dominio remitente:

- `EMAIL_BACKEND=gym_project.gym_app.email_delivery.ResendBackend`
- `RESEND_API_KEY`: clave privada creada en el proveedor, directamente en Railway.
- `DEFAULT_FROM_EMAIL`: remitente de un dominio propio verificado, no @gmail.com.
- `PUBLIC_BASE_URL=https://aware-cooperation-production-fa91.up.railway.app`

Resend exige un dominio propio verificado para enviar a usuarios arbitrarios.
Su remitente de prueba solo envía al correo del titular de la cuenta; no sirve
como configuración final para todos los usuarios. No se ha contratado ni
activado ningún proveedor desde el código.
Fuente: https://resend.com/docs/knowledge-base/403-error-resend-dev-domain

## Diagnóstico desde el servicio desplegado

`python manage.py verificar_correo` valida configuración sin enviar ni mostrar claves.

`python manage.py verificar_correo --destinatario TU_CORREO_DE_PRUEBA`
envía un único mensaje técnico sin token, a un destinatario que controles.
Aceptación del proveedor no garantiza entrega: comprobar entrada/spam y panel del proveedor.
Los códigos HTTP 401/403 indican rechazo de autenticación o permisos/remitente;
429 indica límite del proveedor; CONNECTION_FAILED indica conectividad.
Consultar los detalles en el panel privado del proveedor, nunca pegar claves en el chat.

## SMTP (solo donde esté permitido)

En Railway Pro debe establecerse `RAILWAY_SMTP_ENABLED=True` y redesplegar el servicio.
No habilitarlo en Trial/Hobby: solo evita el chequeo de configuración, no desbloquea la red.

En el servicio del aplicativo, configurar las variables del proveedor SMTP:

- `EMAIL_HOST`: servidor SMTP.
- `EMAIL_PORT`: normalmente 587 con STARTTLS o 465 con SSL, según el proveedor.
- `EMAIL_HOST_USER`: usuario SMTP.
- `EMAIL_HOST_PASSWORD`: clave SMTP o contraseña de aplicación, nunca la contraseña personal.
- `EMAIL_USE_TLS=True` y `EMAIL_USE_SSL=False` para STARTTLS. Para SSL usar False/True. No activar ambas.
- `DEFAULT_FROM_EMAIL`: dirección remitente verificada por el proveedor.
- `PUBLIC_BASE_URL`: URL HTTPS pública del aplicativo, sin rutas. Railway la toma de su dominio público si no se configura esta variable.

No pegar claves en Git ni en mensajes. Introducirlas directamente en Railway → Variables.
Se requiere que el alojamiento permita salida hacia el puerto SMTP elegido.

Tras desplegar, probar con una cuenta propia: solicitar enlace, comprobar entrega (incluido spam), cambiar contraseña y verificar que reutilizar el enlace falla. Las pruebas locales usan una bandeja simulada; no demuestran entrega real del proveedor.

Sin correo configurado se muestra servicio no disponible. Una solicitud válida muestra el mismo mensaje para cuentas existentes e inexistentes. Los errores de envío generan un aviso técnico sin direcciones ni tokens en los logs.
