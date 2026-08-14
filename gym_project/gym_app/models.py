from datetime import timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import (
    FileExtensionValidator,
    MaxValueValidator,
    MinValueValidator,
)
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

class RolChoice(models.TextChoices):
    ADMIN = 'admin', 'Administrador'
    MODERADOR = 'moderador', 'Moderador'
    USUARIO = 'usuario', 'Usuario'

class GeneroChoice(models.TextChoices):
    FEMENINO = 'femenino', 'Femenino'
    MASCULINO = 'masculino', 'Masculino'
    OTRO = 'otro', 'Otro'

class ObjetivoChoice(models.TextChoices):
    ESTETICO = "estetico", "Estético"
    HIPERTROFIA = "hipertrofia", "Hipertrofia"
    SALUD = "salud", "Salud"
    NUTRICION = "nutricion", "Nutrición"
    RECUPERAR = "recuperar", "Recuperación"


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

class EstadoAsignacionChoice(models.TextChoices):
    ACTIVO = "activo", "Activo"
    PAUSADO = "pausado", "Pausado"
    COMPLETADO = "completado", "Completado"
    ABANDONADO = "abandonado", "Abandonado"

class DiaSemanaChoice(models.IntegerChoices):
    LUNES = 0, "Lunes"
    MARTES = 1, "Martes"
    MIERCOLES = 2, "Miércoles"
    JUEVES = 3, "Jueves"
    VIERNES = 4, "Viernes"
    SABADO = 5, "Sábado"
    DOMINGO = 6, "Domingo"

class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    rol = models.CharField(
        max_length=20,
        choices=RolChoice.choices,
        default=RolChoice.USUARIO
    )
    objetivo = models.CharField(
        max_length=50,
        choices=ObjetivoChoice.choices,
        null=True,
        blank=True,
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


class PlanEntrenamiento(models.Model):
    nombre = models.CharField(
        max_length=140,
        unique=True,
    )
    slug = models.SlugField(
        max_length=160,
        unique=True,
        editable=False,
    )
    objetivo = models.CharField(
        max_length=20,
        choices=ObjetivoChoice.choices,
    )
    nivel = models.CharField(
        max_length=20,
        choices=NivelEjercicioChoice.choices,
        default=NivelEjercicioChoice.PRINCIPIANTE,
    )
    descripcion = models.TextField()
    duracion_semanas = models.PositiveSmallIntegerField(
        default=12,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(52),
        ],
    )
    dias_por_semana = models.PositiveSmallIntegerField(
        default=3,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(7),
        ],
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
        ordering = ["objetivo", "nivel", "nombre"]
        verbose_name = "Plan de entrenamiento"
        verbose_name_plural = "Planes de entrenamiento"


class FasePlan(models.Model):
    plan = models.ForeignKey(
        PlanEntrenamiento,
        on_delete=models.CASCADE,
        related_name="fases",
    )
    nombre = models.CharField(max_length=120)
    orden = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(20),
        ],
    )
    semana_inicio = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(52),
        ],
    )
    semana_fin = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(52),
        ],
    )
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)

    def clean(self):
        errores = {}

        if self.semana_inicio > self.semana_fin:
            errores["semana_fin"] = (
                "La semana final no puede ser menor que la inicial."
            )

        if self.plan_id:
            if self.semana_fin > self.plan.duracion_semanas:
                errores["semana_fin"] = (
                    "La fase no puede superar la duración del plan."
                )

            conflicto = FasePlan.objects.filter(
                plan=self.plan,
                semana_inicio__lte=self.semana_fin,
                semana_fin__gte=self.semana_inicio,
            ).exclude(pk=self.pk)

            if conflicto.exists():
                errores["semana_inicio"] = (
                    "Estas semanas se cruzan con otra fase del plan."
                )

        if errores:
            raise ValidationError(errores)

    def __str__(self):
        return (
            f"{self.plan.nombre} - {self.nombre} "
            f"(semanas {self.semana_inicio}-{self.semana_fin})"
        )

    class Meta:
        ordering = ["plan", "orden"]
        constraints = [
            models.UniqueConstraint(
                fields=["plan", "orden"],
                name="fase_orden_unico_por_plan",
            ),
        ]
        verbose_name = "Fase del plan"
        verbose_name_plural = "Fases del plan"


class DiaPlan(models.Model):
    fase = models.ForeignKey(
        FasePlan,
        on_delete=models.CASCADE,
        related_name="dias",
    )
    numero = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(7),
        ],
    )
    nombre = models.CharField(max_length=120)
    enfoque = models.CharField(
        max_length=180,
        blank=True,
    )
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)

    def clean(self):
        if (
            self.fase_id
            and self.numero > self.fase.plan.dias_por_semana
        ):
            raise ValidationError({
                "numero": (
                    "El número del día supera los días semanales del plan."
                )
            })

    def __str__(self):
        return (
            f"{self.fase.plan.nombre} - "
            f"{self.fase.nombre} - "
            f"Día {self.numero}: {self.nombre}"
        )

    class Meta:
        ordering = ["fase", "numero"]
        constraints = [
            models.UniqueConstraint(
                fields=["fase", "numero"],
                name="dia_numero_unico_por_fase",
            ),
        ]
        verbose_name = "Día del plan"
        verbose_name_plural = "Días del plan"

class EjercicioProgramado(models.Model):
    dia = models.ForeignKey(
        DiaPlan,
        on_delete=models.CASCADE,
        related_name="ejercicios_programados",
    )
    ejercicio = models.ForeignKey(
        Ejercicio,
        on_delete=models.PROTECT,
        related_name="programaciones",
    )
    orden = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(50),
        ],
    )
    series = models.PositiveSmallIntegerField(
        default=3,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(20),
        ],
    )

    repeticiones_min = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(1000),
        ],
    )
    repeticiones_max = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(1000),
        ],
    )
    duracion_segundos = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(7200),
        ],
    )
    distancia_metros = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(100000),
        ],
    )

    descanso_segundos = models.PositiveSmallIntegerField(
        default=60,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(1800),
        ],
    )
    esfuerzo_objetivo = models.PositiveSmallIntegerField(
        default=7,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(10),
        ],
        help_text=(
            "Esfuerzo percibido del 1 al 10. "
            "Un valor de 7 significa esfuerzo moderado-alto."
        ),
    )
    obligatorio = models.BooleanField(default=True)
    notas = models.TextField(blank=True)
    activo = models.BooleanField(default=True)

    def clean(self):
        errores = {}

        if (
            self.repeticiones_min is not None
            and self.repeticiones_max is not None
            and self.repeticiones_min > self.repeticiones_max
        ):
            errores["repeticiones_max"] = (
                "Las repeticiones máximas no pueden ser menores "
                "que las mínimas."
            )

        if self.ejercicio_id:
            medicion = self.ejercicio.tipo_medicion

            if medicion == TipoMedicionChoice.REPETICIONES:
                if self.repeticiones_min is None:
                    errores["repeticiones_min"] = (
                        "Este ejercicio necesita repeticiones mínimas."
                    )

                if self.repeticiones_max is None:
                    errores["repeticiones_max"] = (
                        "Este ejercicio necesita repeticiones máximas."
                    )

                if self.duracion_segundos is not None:
                    errores["duracion_segundos"] = (
                        "Déjalo vacío para ejercicios por repeticiones."
                    )

                if self.distancia_metros is not None:
                    errores["distancia_metros"] = (
                        "Déjalo vacío para ejercicios por repeticiones."
                    )

            elif medicion == TipoMedicionChoice.TIEMPO:
                if self.duracion_segundos is None:
                    errores["duracion_segundos"] = (
                        "Este ejercicio necesita una duración."
                    )

                if (
                    self.repeticiones_min is not None
                    or self.repeticiones_max is not None
                ):
                    errores["repeticiones_min"] = (
                        "Las repeticiones deben quedar vacías."
                    )

                if self.distancia_metros is not None:
                    errores["distancia_metros"] = (
                        "La distancia debe quedar vacía."
                    )

            elif medicion == TipoMedicionChoice.DISTANCIA:
                if self.distancia_metros is None:
                    errores["distancia_metros"] = (
                        "Este ejercicio necesita una distancia."
                    )

                if (
                    self.repeticiones_min is not None
                    or self.repeticiones_max is not None
                ):
                    errores["repeticiones_min"] = (
                        "Las repeticiones deben quedar vacías."
                    )

                if self.duracion_segundos is not None:
                    errores["duracion_segundos"] = (
                        "La duración debe quedar vacía."
                    )

        if errores:
            raise ValidationError(errores)

    def __str__(self):
        return (
            f"{self.dia} - "
            f"{self.orden}. {self.ejercicio.nombre}"
        )

    class Meta:
        ordering = ["dia", "orden"]
        constraints = [
            models.UniqueConstraint(
                fields=["dia", "orden"],
                name="ejercicio_orden_unico_por_dia",
            ),
            models.UniqueConstraint(
                fields=["dia", "ejercicio"],
                name="ejercicio_unico_por_dia",
            ),
        ]
        verbose_name = "Ejercicio programado"
        verbose_name_plural = "Ejercicios programados"

class AsignacionPlanUsuario(models.Model):
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="planes_asignados",
    )
    plan = models.ForeignKey(
        PlanEntrenamiento,
        on_delete=models.PROTECT,
        related_name="asignaciones",
    )
    fecha_inicio = models.DateField(
        default=timezone.localdate,
    )
    fecha_fin = models.DateField(
        null=True,
        blank=True,
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoAsignacionChoice.choices,
        default=EstadoAsignacionChoice.ACTIVO,
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    @property
    def fecha_fin_estimada(self):
        return (
            self.fecha_inicio
            + timedelta(weeks=self.plan.duracion_semanas)
            - timedelta(days=1)
        )

    @property
    def semana_actual(self):
        hoy = timezone.localdate()

        if hoy < self.fecha_inicio:
            return 0

        dias_transcurridos = (hoy - self.fecha_inicio).days
        semana = (dias_transcurridos // 7) + 1

        return min(
            semana,
            self.plan.duracion_semanas,
        )

    @property
    def fase_actual(self):
        semana = self.semana_actual

        if semana == 0:
            return None

        return self.plan.fases.filter(
            semana_inicio__lte=semana,
            semana_fin__gte=semana,
            activo=True,
        ).first()

    def clean(self):
        errores = {}

        if (
            self.fecha_fin is not None
            and self.fecha_fin < self.fecha_inicio
        ):
            errores["fecha_fin"] = (
                "La fecha final no puede ser anterior al inicio."
            )

        if (
            self.usuario_id
            and self.estado == EstadoAsignacionChoice.ACTIVO
        ):
            otra_asignacion = AsignacionPlanUsuario.objects.filter(
                usuario=self.usuario,
                estado=EstadoAsignacionChoice.ACTIVO,
            ).exclude(pk=self.pk)

            if otra_asignacion.exists():
                errores["estado"] = (
                    "El usuario ya tiene otro plan activo."
                )

        if errores:
            raise ValidationError(errores)

    def __str__(self):
        return (
            f"{self.usuario.get_full_name() or self.usuario.username} - "
            f"{self.plan.nombre}"
        )

    class Meta:
        ordering = [
            "-fecha_inicio",
            "usuario",
        ]
        verbose_name = "Plan asignado a usuario"
        verbose_name_plural = "Planes asignados a usuarios"

class HorarioPlanUsuario(models.Model):
    asignacion = models.ForeignKey(
        AsignacionPlanUsuario,
        on_delete=models.CASCADE,
        related_name="horarios",
    )
    numero_dia_plan = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(7),
        ],
    )
    dia_semana = models.PositiveSmallIntegerField(
        choices=DiaSemanaChoice.choices,
    )
    hora_preferida = models.TimeField(
        null=True,
        blank=True,
    )
    recordatorio_activo = models.BooleanField(default=True)
    activo = models.BooleanField(default=True)

    def clean(self):
        if (
            self.asignacion_id
            and self.numero_dia_plan
            > self.asignacion.plan.dias_por_semana
        ):
            raise ValidationError({
                "numero_dia_plan": (
                    "Este número supera los días semanales del plan."
                )
            })

    def __str__(self):
        return (
            f"{self.asignacion.usuario.username} - "
            f"Día {self.numero_dia_plan} del plan: "
            f"{self.get_dia_semana_display()}"
        )

    class Meta:
        ordering = [
            "asignacion",
            "dia_semana",
        ]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "asignacion",
                    "numero_dia_plan",
                ],
                name="numero_dia_unico_por_asignacion",
            ),
            models.UniqueConstraint(
                fields=[
                    "asignacion",
                    "dia_semana",
                ],
                name="dia_semana_unico_por_asignacion",
            ),
        ]
        verbose_name = "Horario del plan"
        verbose_name_plural = "Horarios del plan"