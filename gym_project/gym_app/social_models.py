import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


class GrupoAmigos(models.Model):
    nombre = models.CharField(max_length=80)
    imagen = models.ImageField(upload_to='grupos/', blank=True)
    administrador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    invitacion = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    creado = models.DateTimeField(auto_now_add=True)


class IntegranteGrupo(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    grupo = models.ForeignKey(GrupoAmigos, on_delete=models.CASCADE, related_name='integrantes')
    desde = models.DateTimeField(auto_now_add=True)


class RecompensaEjercicio(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    registro = models.OneToOneField('gym_app.EjercicioSesion', on_delete=models.PROTECT)
    ejercicio = models.ForeignKey('gym_app.Ejercicio', on_delete=models.PROTECT)
    fecha = models.DateField()
    puntos = models.PositiveIntegerField()
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['usuario', 'ejercicio', 'fecha'], name='recompensa_ejercicio_usuario_dia')]


class DiaComprometido(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    fecha = models.DateField()
    cancelado = models.BooleanField(default=False)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['usuario', 'fecha'], name='compromiso_usuario_fecha')]


class RutinaGrupal(models.Model):
    grupo = models.ForeignKey(GrupoAmigos, on_delete=models.CASCADE, related_name='rutinas')
    titulo = models.CharField(max_length=100)
    fecha = models.DateField()
    hora = models.TimeField(null=True, blank=True)
    ejercicios = models.ManyToManyField('gym_app.Ejercicio')
    revision = models.PositiveIntegerField(default=1)


class ParticipacionGrupal(models.Model):
    rutina = models.ForeignKey(RutinaGrupal, on_delete=models.CASCADE, related_name='participaciones')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    revision = models.PositiveIntegerField()
    sesion = models.OneToOneField('gym_app.SesionEntrenamiento', null=True, blank=True, on_delete=models.PROTECT)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['rutina', 'usuario'], name='participacion_unica')]


class AvisoSocial(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    texto = models.CharField(max_length=250)
    creado = models.DateTimeField(default=timezone.now)


class ResultadoGrupo(models.Model):
    grupo = models.ForeignKey(GrupoAmigos, on_delete=models.CASCADE)
    semana = models.DateField()
    clasificacion = models.JSONField(default=list)
    insignia = models.BooleanField(default=False)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['grupo', 'semana'], name='resultado_grupo_semana')]
