from datetime import date
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase, SimpleTestCase
from django.urls import reverse
from django.utils import timezone

from .models import (PerfilUsuario, Ejercicio, RecompensaEjercicio,
                     GrupoAmigos, IntegranteGrupo, RutinaGrupal, ParticipacionGrupal)
from .services import (_convertir_decimal, crear_rutina_personalizada,
                       iniciar_sesion_entrenamiento, iniciar_serie_entrenamiento,
                       completar_serie_entrenamiento, omitir_descanso_serie)
from .social_services import comenzar_grupal


class RegistroRobustoTest(TestCase):
    def datos(self, **cambios):
        datos = dict(nombre='Prueba', apellido='Auditoria',
                     email='auditoria@example.com', password='Prueba-Segura-872!',
                     confirmar_password='Prueba-Segura-872!',
                     fecha_nacimiento='2000-01-01', enfoque_corporal='full_body')
        datos.update(cambios)
        return datos

    def test_campos_obligatorios_se_validan_en_servidor(self):
        for campo in ('nombre', 'apellido'):
            with self.subTest(campo=campo):
                respuesta = self.client.post(reverse('registrarse'), self.datos(**{campo: ' '}))
                self.assertEqual(respuesta.status_code, 200)
                self.assertFalse(User.objects.exists())

    def test_longitudes_invalidas_no_dejan_cuenta_parcial(self):
        for campos in ({'nombre': 'x' * 151}, {'apellido': 'x' * 151},
                       {'documento': '1' * 41, 'tipo_documento': 'CC'},
                       {'telefono': '1' * 31}, {'direccion': 'x' * 161}):
            with self.subTest(campos=list(campos)):
                respuesta = self.client.post(reverse('registrarse'), self.datos(**campos))
                self.assertEqual(respuesta.status_code, 200)
                self.assertFalse(User.objects.exists())

    def test_fallo_al_guardar_perfil_revierte_creacion_de_usuario(self):
        guardar = PerfilUsuario.save

        def fallo(perfil, *args, **kwargs):
            if kwargs.get('update_fields'):
                raise IntegrityError('Fallo de guardado simulado')
            return guardar(perfil, *args, **kwargs)

        with patch.object(PerfilUsuario, 'save', fallo):
            respuesta = self.client.post(reverse('registrarse'), self.datos())
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(User.objects.exists())

    def test_correo_en_conflicto_durante_creacion_muestra_error(self):
        with patch.object(User.objects, 'create_user', side_effect=IntegrityError('Duplicado')):
            respuesta = self.client.post(reverse('registrarse'), self.datos())
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'correo')


class ValoresEntrenamientoTest(SimpleTestCase):
    def test_peso_no_finito_se_rechaza_como_error_de_validacion(self):
        for valor in ('NaN', 'sNaN', 'Infinity', '-Infinity'):
            with self.subTest(valor=valor):
                with self.assertRaises(ValidationError):
                    _convertir_decimal(valor, 'el peso utilizado')


class PaginasUsuarioTest(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('recorrido', password='Prueba-Segura-872!')
        perfil = self.usuario.perfil
        perfil.objetivo = 'salud'
        perfil.nivel_declarado = perfil.nivel_entrenamiento = 'principiante'
        perfil.prueba_nivel_completada = perfil.configuracion_entrenamiento_completa = True
        perfil.orientacion_nutricional_vista = perfil.datos_completos = True
        perfil.fecha_nacimiento = date(2000, 1, 1)
        perfil.peso = 75
        perfil.altura_cm = 175
        perfil.save()

    def test_paginas_publicas_y_autenticadas_renderizan(self):
        for nombre in ('inicio', 'escogenos', 'precios', 'registrarse', 'login',
                       'rutinas', 'salud', 'hipertrofia', 'estetico', 'nutricion',
                       'contacto', 'privacidad', 'password_reset'):
            with self.subTest(nombre=nombre):
                self.assertEqual(self.client.get(reverse(nombre)).status_code, 200)
        self.client.force_login(self.usuario)
        for nombre in ('cuenta', 'preferencias', 'modificar_rutina', 'mi_entrenamiento',
                       'amigos', 'notificaciones', 'dieta', 'cambiar_password',
                       'configurar_rutina', 'revisar_registro'):
            with self.subTest(nombre=nombre):
                self.assertEqual(self.client.get(reverse(nombre)).status_code, 200)

    def test_usuario_normal_no_accede_a_paneles(self):
        self.client.force_login(self.usuario)
        for nombre in ('panel_admin', 'panel_moderador'):
            self.assertEqual(self.client.get(reverse(nombre)).status_code, 403)

    def test_genero_invalido_no_completa_datos_personales(self):
        perfil = self.usuario.perfil
        perfil.datos_completos = False
        perfil.save(update_fields=['datos_completos'])
        self.client.force_login(self.usuario)
        respuesta = self.client.post(reverse('datos_personales'),
                                    {'genero': 'inventado', 'peso': '75', 'altura_cm': '175'})
        self.assertEqual(respuesta.status_code, 400)
        perfil.refresh_from_db()
        self.assertFalse(perfil.datos_completos)


class SesionesCompletasTest(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('sesiones', password='Prueba-Segura-872!')
        perfil = self.usuario.perfil
        perfil.objetivo = 'salud'
        perfil.nivel_declarado = perfil.nivel_entrenamiento = 'principiante'
        perfil.prueba_nivel_completada = perfil.configuracion_entrenamiento_completa = True
        perfil.orientacion_nutricional_vista = perfil.datos_completos = True
        perfil.save()
        self.client.force_login(self.usuario)

    def sesion(self, tipo='repeticiones'):
        ejercicio = Ejercicio.objects.create(
            nombre=f'Ejercicio auditoría {tipo}', grupo_muscular='pecho',
            nivel='principiante', tipo_equipo='peso_corporal', tipo_medicion=tipo,
            puntos_base=10)
        asignacion = crear_rutina_personalizada(self.usuario, 'salud', 'principiante',
            [timezone.localdate().weekday()], [dict(dia=1, ejercicio_id=ejercicio.pk,
            cantidad=10, series=2, descanso=15)])
        sesion, _ = iniciar_sesion_entrenamiento(asignacion, asignacion.plan.fases.get().dias.get())
        return sesion

    def test_recorrido_por_series_repeticiones_tiempo_y_distancia(self):
        # Usuarios separados: solo puede existir un entrenamiento diario por persona.
        for tipo, campo in (('repeticiones', 'repeticiones_realizadas'),
                            ('tiempo', 'duracion_realizada_segundos'),
                            ('distancia', 'distancia_realizada_metros')):
            with self.subTest(tipo=tipo):
                if tipo != 'repeticiones':
                    self.usuario = User.objects.create_user('sesiones-' + tipo)
                    self.client.force_login(self.usuario)
                sesion = self.sesion(tipo)
                url = reverse('reproductor_entrenamiento', args=[sesion.pk])
                self.assertEqual(self.client.get(url).status_code, 200)
                series = list(sesion.ejercicios.get().series.order_by('numero'))
                for indice, serie in enumerate(series):
                    iniciar_serie_entrenamiento(self.usuario, serie.pk)
                    resultado = completar_serie_entrenamiento(self.usuario, serie.pk, **{campo: 10})
                    self.assertTrue(resultado[1])
                    self.assertFalse(completar_serie_entrenamiento(self.usuario, serie.pk, **{campo: 10})[1])
                    if indice == 0:
                        with self.assertRaises(ValidationError):
                            iniciar_serie_entrenamiento(self.usuario, series[1].pk)
                        omitir_descanso_serie(self.usuario, serie.pk)
                sesion.refresh_from_db()
                registro = sesion.ejercicios.get()
                self.assertEqual(sesion.estado, 'completada')
                self.assertEqual(sesion.puntos_obtenidos, 10)
                self.assertEqual(getattr(registro, campo), 20)
                self.assertEqual(RecompensaEjercicio.objects.filter(usuario=self.usuario).count(), 1)
                self.assertContains(self.client.get(url), 'Entrenamiento completado')

    def test_serie_ajena_no_se_puede_completar(self):
        sesion = self.sesion()
        serie = sesion.ejercicios.get().series.first()
        otro = User.objects.create_user('ajeno')
        with self.assertRaises(ValidationError):
            iniciar_serie_entrenamiento(otro, serie.pk)
        self.client.force_login(otro)
        self.assertEqual(self.client.post(reverse('reproductor_entrenamiento', args=[sesion.pk]),
            {'accion': 'iniciar_serie', 'serie_id': serie.pk}).status_code, 302)
        serie.refresh_from_db()
        self.assertEqual(serie.estado, 'pendiente')

    def test_eliminar_cuenta_con_sesion_grupal_y_recompensas(self):
        personal = self.sesion()
        # Liberar el día para la propuesta grupal, conservando el plan personal.
        personal.delete()
        grupo = GrupoAmigos.objects.create(nombre='Auditoría', administrador=self.usuario)
        IntegranteGrupo.objects.create(grupo=grupo, usuario=self.usuario)
        rutina = RutinaGrupal.objects.create(grupo=grupo, titulo='Prueba', fecha=timezone.localdate())
        rutina.ejercicios.add(Ejercicio.objects.get(nombre='Ejercicio auditoría repeticiones'))
        ParticipacionGrupal.objects.create(rutina=rutina, usuario=self.usuario, revision=rutina.revision)
        sesion = comenzar_grupal(self.usuario, rutina)
        for serie in sesion.ejercicios.get().series.order_by('numero'):
            iniciar_serie_entrenamiento(self.usuario, serie.pk)
            completar_serie_entrenamiento(self.usuario, serie.pk, repeticiones_realizadas=12)
            omitir_descanso_serie(self.usuario, serie.pk)
        self.assertTrue(RecompensaEjercicio.objects.filter(usuario=self.usuario).exists())
        respuesta = self.client.post(reverse('cuenta'),
            {'accion': 'eliminar_cuenta', 'password_actual': 'Prueba-Segura-872!'})
        self.assertEqual(respuesta.url, reverse('inicio'))
        self.assertFalse(User.objects.filter(pk=self.usuario.pk).exists())
        self.assertFalse(GrupoAmigos.objects.filter(pk=grupo.pk).exists())
