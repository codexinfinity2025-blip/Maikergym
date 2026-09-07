from datetime import timedelta
from uuid import uuid4
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone
from .models import (PerfilUsuario, GrupoAmigos, IntegranteGrupo, RutinaGrupal,
    ParticipacionGrupal, Ejercicio, DiaComprometido, SesionEntrenamiento, RecompensaEjercicio)
from .services import crear_rutina_automatica, completar_ejercicio_sesion, iniciar_sesion_entrenamiento
from .social_services import unirse, comenzar_grupal, resumen_usuario


class SocialTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('cargar_ejercicios', verbosity=0)

    def setUp(self):
        self.usuario = self.nuevo_usuario('principal')
        self.grupo = GrupoAmigos.objects.create(nombre='Equipo', administrador=self.usuario)
        IntegranteGrupo.objects.create(usuario=self.usuario, grupo=self.grupo)
        self.client.force_login(self.usuario)

    def nuevo_usuario(self, nombre):
        u = User.objects.create_user(username=nombre)
        p = PerfilUsuario.objects.get(user=u)
        p.objetivo = 'salud'
        p.nivel_entrenamiento = p.nivel_declarado = 'principiante'
        p.prueba_nivel_completada = p.configuracion_entrenamiento_completa = True
        p.orientacion_nutricional_vista = p.datos_completos = True
        p.save()
        return u

    def test_limite_y_grupo_unico(self):
        for i in range(6):
            unirse(self.nuevo_usuario(f'amigo{i}'), self.grupo.invitacion)
        with self.assertRaises(ValidationError):
            unirse(self.nuevo_usuario('octavo'), self.grupo.invitacion)
        with self.assertRaises(ValidationError):
            unirse(self.usuario, self.grupo.invitacion)
        self.assertEqual(self.grupo.integrantes.count(), 7)

    def test_permisos_y_pantallas(self):
        self.assertEqual(self.client.get(reverse('amigos')).status_code, 200)
        self.assertEqual(self.client.get(reverse('nueva_rutina_grupal')).status_code, 200)
        intruso = self.nuevo_usuario('intruso')
        grupo = GrupoAmigos.objects.create(nombre='Ajeno', administrador=intruso)
        rutina = RutinaGrupal.objects.create(grupo=grupo, titulo='Privada', fecha=timezone.localdate())
        self.assertEqual(self.client.get(reverse('rutina_grupal', args=[rutina.pk])).status_code, 404)

    def test_grupal_usa_reproductor_y_no_duplica_sesion_ni_puntos(self):
        hoy = timezone.localdate()
        asignacion = crear_rutina_automatica(self.usuario, 'salud', 'principiante', [hoy.weekday()], 60, 60)
        rutina = RutinaGrupal.objects.create(grupo=self.grupo, titulo='Juntos', fecha=hoy)
        ejercicio = Ejercicio.objects.filter(activo=True, nivel='principiante', tipo_medicion='repeticiones').first()
        rutina.ejercicios.add(ejercicio)
        ParticipacionGrupal.objects.create(usuario=self.usuario, rutina=rutina, revision=rutina.revision)
        sesion = comenzar_grupal(self.usuario, rutina)
        self.assertEqual(comenzar_grupal(self.usuario, rutina).pk, sesion.pk)
        normal, _ = iniciar_sesion_entrenamiento(asignacion, asignacion.plan.fases.get().dias.get())
        self.assertEqual(normal.pk, sesion.pk)
        self.assertEqual(self.client.get(reverse('reproductor_entrenamiento', args=[sesion.pk])).status_code, 200)
        registro = sesion.ejercicios.get()
        argumentos = dict(usuario=self.usuario, ejercicio_sesion_id=registro.pk, series_completadas=registro.ejercicio_programado.series, repeticiones_realizadas=12)
        completar_ejercicio_sesion(**argumentos)
        completar_ejercicio_sesion(**argumentos)
        sesion.refresh_from_db()
        self.assertEqual(sesion.puntos_obtenidos, ejercicio.puntos_base)
        self.assertEqual(RecompensaEjercicio.objects.filter(usuario=self.usuario).count(), 1)
        self.assertEqual(resumen_usuario(self.usuario)['racha'], 1)

    def test_cambio_calendario_conserva_pasado(self):
        ayer = timezone.localdate() - timedelta(days=1)
        DiaComprometido.objects.create(usuario=self.usuario, fecha=ayer)
        crear_rutina_automatica(self.usuario, 'salud', 'principiante', [timezone.localdate().weekday()], 60, 60)
        self.assertFalse(DiaComprometido.objects.get(usuario=self.usuario, fecha=ayer).cancelado)

    def test_enfoque_inferior_conserva_torso(self):
        a = crear_rutina_automatica(self.usuario, 'salud', 'principiante', [0, 2, 4], 60, 60, priorizar_tren_inferior=True)
        nombres = list(a.plan.fases.get().dias.order_by('numero').values_list('nombre', flat=True))
        self.assertEqual(nombres, ['Piernas y glúteos', 'Tren superior', 'Tren inferior'])
