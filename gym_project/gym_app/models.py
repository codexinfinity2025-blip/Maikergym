from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.utils.text import slugify

class RolChoice(models.TextChoices):
    ADMIN = 'admin', 'Administrador'
    MODERADOR = 'moderador', 'Moderador'
    USUARIO = 'usuario', 'Usuario'

class GeneroChoice(models.TextChoices):
    FEMENINO = 'femenino', 'Femenino'
    MASCULINO = 'masculino', 'Masculino'
    OTRO = 'otro', 'Otro'


class GrupoMuscularChoice(models.TextChoices):
    PECHO = "pecho", "Pecho"
    ESPALDA = "espalda", "Espalda"
    HOMBROS = "hombros", "Hombros"
    BICEPS = "biceps", "Bíceps"
    TRICEPS = "triceps", "Tríceps"
    CUADRICEPS = "cuadriceps", "Cuádriceps"
    FEMORALES = "femorales", "Femorales"
    GLUTEOS = "gluteos", "Glúteos"
    PANTORRILLAS = "pantorrillas", "Pantorrillas"
    ABDOMEN = "abdomen", "Abdomen"
    CUERPO_COMPLETO = "cuerpo_completo", "Cuerpo completo"
    CARDIO = "cardio", "Cardio"


class NivelEjercicioChoice(models.TextChoices):
    PRINCIPIANTE = "principiante", "Principiante"
    INTERMEDIO = "intermedio", "Intermedio"
    AVANZADO = "avanzado", "Avanzado"


class TipoEquipoChoice(models.TextChoices):
    BARRA = "barra", "Barra"
    MANCUERNAS = "mancuernas", "Mancuernas"
    MAQUINA = "maquina", "Máquina"
    POLEA = "polea", "Polea"
    PESO_CORPORAL = "peso_corporal", "Peso corporal"
    BANDA_ELASTICA = "banda_elastica", "Banda elástica"
    KETTLEBELL = "kettlebell", "Kettlebell"
    CARDIO = "cardio", "Máquina de cardio"
    OTRO = "otro", "Otro"

class TipoMedicionChoice(models.TextChoices):
    REPETICIONES = "repeticiones", "Repeticiones"
    TIEMPO = "tiempo", "Tiempo"
    DISTANCIA = "distancia", "Distancia"

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
    @property
    def foto_disponible(self):
        if not self.foto:
            return False

        try:
            return self.foto.storage.exists(self.foto.name)
        except (OSError, ValueError):
            return False

    def personalizacion_completa(self):
        return bool(self.objetivo and self.dieta_aceptada and self.datos_completos)

    def __str__(self):
        return f"{self.user.email} - {self.get_rol_display()}"

    class Meta:
        verbose_name = 'Perfil Usuario'
        verbose_name_plural = 'Perfiles Usuarios'


class Ejercicio(models.Model):
    nombre = models.CharField(
        max_length=120,
        unique=True
    )
    slug = models.SlugField(
        max_length=140,
        unique=True,
        editable=False
    )
    descripcion = models.TextField()
    instrucciones = models.TextField(
        help_text="Escribe un paso de ejecución por cada línea."
    )
    errores_comunes = models.TextField(
        blank=True
    )
    precauciones = models.TextField(
        blank=True
    )

    grupo_muscular = models.CharField(
        max_length=30,
        choices=GrupoMuscularChoice.choices
    )
    musculos_secundarios = models.CharField(
        max_length=180,
        blank=True
    )
    nivel = models.CharField(
        max_length=20,
        choices=NivelEjercicioChoice.choices,
        default=NivelEjercicioChoice.PRINCIPIANTE
    )
    tipo_equipo = models.CharField(
        max_length=30,
        choices=TipoEquipoChoice.choices
    )
    equipo_necesario = models.CharField(
        max_length=180,
        blank=True
    )
    tipo_medicion = models.CharField(
        max_length=20,
        choices=TipoMedicionChoice.choices,
        default=TipoMedicionChoice.REPETICIONES
    )

    puntos_base = models.PositiveSmallIntegerField(
        default=10
    )
    imagen_portada = models.ImageField(
        upload_to="ejercicios/portadas/",
        null=True,
        blank=True
    )
    modelo_3d = models.FileField(
        upload_to="ejercicios/modelos_3d/",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["glb", "gltf"]
            )
        ],
        null=True,
        blank=True
    )

    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ["grupo_muscular", "nombre"]
        verbose_name = "Ejercicio"
        verbose_name_plural = "Ejercicios"