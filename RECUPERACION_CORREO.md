# Activar recuperación en Railway

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
