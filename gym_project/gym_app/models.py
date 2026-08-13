from django.db import models
from django.contrib.auth.models import User

class RolChoice(models.TextChoices):
    ADMIN = 'admin', 'Administrador'
    MODERADOR = 'moderador', 'Moderador'
    USUARIO = 'usuario', 'Usuario'

class GeneroChoice(models.TextChoices):
    FEMENINO = 'femenino', 'Femenino'
    MASCULINO = 'masculino', 'Masculino'
    OTRO = 'otro', 'Otro'

class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    rol = models.CharField(
        max_length=20,
        choices=RolChoice.choices,
        default=RolChoice.USUARIO
    )
    objetivo = models.CharField(
        max_length=50,
        choices=[
            ('estetico', 'Estético'),
            ('hipertrofia', 'Hipertrofia'),
            ('salud', 'Salud'),
            ('nutricion', 'Nutrición'),
            ('recuperar', 'Recuperación'),
        ],
        null=True,
        blank=True
    )
    dieta_aceptada = models.BooleanField(default=False)
    foto = models.ImageField(upload_to='perfiles/', null=True, blank=True)
    telefono = models.CharField(max_length=30, null=True, blank=True)
    direccion = models.CharField(max_length=160, null=True, blank=True)
    peso_inicial = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    genero = models.CharField(max_length=20, choices=GeneroChoice.choices, null=True, blank=True)
    peso = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    edad = models.PositiveIntegerField(null=True, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    datos_completos = models.BooleanField(default=False)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    def personalizacion_completa(self):
        return bool(self.objetivo and self.dieta_aceptada and self.datos_completos)

    def __str__(self):
        return f"{self.user.email} - {self.get_rol_display()}"

    class Meta:
        verbose_name = 'Perfil Usuario'
        verbose_name_plural = 'Perfiles Usuarios'