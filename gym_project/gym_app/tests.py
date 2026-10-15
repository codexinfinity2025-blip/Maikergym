from datetime import date, timedelta
from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.contrib.auth.models import User
from django.core.management import call_command
from django.db import IntegrityError
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

from .models import (
    AsignacionPlanUsuario,
    Ejercicio,
    EstadoAsignacionChoice,
    EstadoSesionChoice,
    ObjetivoChoice,
    PerfilUsuario,
    PlanEntrenamiento,
    SesionEntrenamiento,
)
from .wellness_content import (
    MENSAJES_MOTIVACIONALES,
    NUTRICION_POR_OBJETIVO,
    obtener_guia_nutricional,
    obtener_mensajes_del_dia,
)
from .services import (
    _segundos_estimados,
    crear_rutina_automatica,
    crear_rutina_personalizada,
)
from .routine_edit import entrenamiento_en_curso
from .profile_validation import estimar_grasa_navy


class FlujoRegistroTest(TestCase):
    def test_sugerencias_alimentos_y_dos_platos_por_comida(self):
        for objetivo in ObjetivoChoice.values:
            guia = obtener_guia_nutricional(objetivo)
            self.assertEqual(len(guia['dias']), 7)
            platos = []
            for dia in guia['dias']:
                self.assertEqual(len(dia['comidas']), 4)
                for comida in dia['comidas']:
                    self.assertGreaterEqual(len(comida['alimentos']), 3)
                    self.assertEqual(len(comida['opciones']), 2)
                    platos.extend(comida['opciones'])
            self.assertEqual(len(platos), len(set(platos)))

    def test_mensajes_se_entregan_separados_y_se_conservan(self):
        usuario = User.objects.create_user(username='avisos')
        self.client.force_login(usuario)
        for hora, esperado in [(8, True), (8, False), (14, True), (14, False), (20, True), (21, False)]:
            ahora = datetime(2026, 9, 7, hora, tzinfo=ZoneInfo('America/Bogota'))
            with patch('gym_project.gym_app.views.timezone.localtime', return_value=ahora):
                resultado = self.client.post(reverse('siguiente_mensaje')).json()
                self.assertEqual(bool(resultado['mensaje']), esperado)
        perfil = PerfilUsuario.objects.get(user=usuario)
        self.assertEqual(len(perfil.mensajes_entregados), 3)
        self.assertNotContains(self.client.get(reverse('notificaciones')), '70 mensajes')


    def test_evaluacion_corporal_no_inventa_meta(self):
        usuario = User.objects.create_user(username='altura')
        perfil = PerfilUsuario.objects.get(user=usuario)
        perfil.peso = 75
        perfil.altura_cm = 175
        perfil.fecha_nacimiento = date(1990, 1, 1)
        perfil.porcentaje_grasa_estimado = 15
        perfil.metodo_estimacion_grasa = "visual"
        resultado = perfil.evaluacion_corporal_interna()
        self.assertEqual(resultado['imc'], 24.49)
        self.assertEqual(resultado['masa_grasa_estimada_kg'], 11.2)
        self.assertEqual(resultado['masa_sin_grasa_estimada_kg'], 63.8)
        self.assertIsNone(resultado['brecha_objetivo'])

    def test_formula_navy_valida_y_rechaza_medidas_imposibles(self):
        porcentaje = estimar_grasa_navy('masculino', 175, 85, 38)
        self.assertGreaterEqual(porcentaje, 2)
        self.assertLessEqual(porcentaje, 60)
        with self.assertRaises(ValidationError):
            estimar_grasa_navy('masculino', 175, 30, 38)

    def test_generador_respeta_nivel_presupuesto_y_dias(self):
        usuario = User.objects.create_user(username="presupuesto")
        for objetivo in ObjetivoChoice.values:
            for cantidad in range(1, 7):
                with self.subTest(objetivo=objetivo, dias=cantidad):
                    asignacion = crear_rutina_automatica(
                        usuario, objetivo, "principiante", list(range(cantidad)), 45, 120,
                        minutos_por_dia={"0": 90},
                    )
                    self.assertEqual(asignacion.horarios.count(), cantidad)
                    for dia in asignacion.plan.fases.get().dias.all():
                        programas = list(dia.ejercicios_programados.select_related("ejercicio"))
                        self.assertGreaterEqual(len(programas), 3)
                        self.assertTrue(all(p.ejercicio.nivel == "principiante" for p in programas))
                        duracion = 600 + sum(_segundos_estimados({
                            "series": p.series, "descanso_segundos": p.descanso_segundos,
                            "duracion_segundos": p.duracion_segundos,
                            "distancia_metros": p.distancia_metros or 0,
                            "repeticiones_max": p.repeticiones_max or 0,
                        }) for p in programas)
                        self.assertLessEqual(duracion, (90 if dia.numero == 1 else 45) * 60)
        self.assertEqual(AsignacionPlanUsuario.objects.filter(usuario=usuario, estado="activo").count(), 1)

    def test_preferencias_invalidas_no_crean_planes(self):
        usuario = User.objects.create_user(username="invalido")
        antes = PlanEntrenamiento.objects.count()
        for dias, minutos, descanso in [([0, 0], 60, 60), ([8], 60, 60), ([0], 44, 60), ([0], 45, 1800)]:
            with self.assertRaises(ValidationError):
                crear_rutina_automatica(usuario, "salud", "principiante", dias, minutos, descanso)
        self.assertEqual(PlanEntrenamiento.objects.count(), antes)

    def test_paginas_personalizacion_renderizan(self):
        usuario = User.objects.create_user(username="paginas")
        perfil = PerfilUsuario.objects.get(user=usuario)
        perfil.objetivo = "salud"
        perfil.nivel_declarado = "intermedio"
        perfil.nivel_entrenamiento = "intermedio"
        perfil.prueba_nivel_completada = True
        perfil.modalidad_rutina = "personalizada"
        perfil.dias_entrenamiento = [0, 3]
        perfil.save()
        self.client.force_login(usuario)
        for ruta in ("nivel_entrenamiento", "prueba_nivel", "configurar_rutina", "crear_rutina", "dieta", "notificaciones"):
            with self.subTest(ruta=ruta):
                self.assertEqual(self.client.get(reverse(ruta)).status_code, 200)

    @classmethod
    def setUpTestData(cls):
        call_command("cargar_ejercicios", verbosity=0)
        call_command("cargar_plan_hipertrofia", verbosity=0)

    def test_hay_un_plan_inicial_para_cada_objetivo(self):
        objetivos_disponibles = set(
            PlanEntrenamiento.objects.filter(
                activo=True,
            ).values_list("objetivo", flat=True)
        )
        self.assertEqual(
            objetivos_disponibles,
            set(ObjetivoChoice.values),
        )

    def test_catalogo_ampliado_y_planes_con_rutinas_propias(self):
        nuevos = {
            "Sentadilla goblet con mancuerna",
            "Zancada estática con mancuernas",
            "Step-up al banco",
            "Puente de glúteos en suelo",
            "Press de pecho sentado en máquina",
            "Face pull en polea",
            "Curl de bíceps en polea baja",
            "Extensión de tríceps sobre la cabeza en polea",
            "Press Pallof en polea",
            "Bird dog",
        }
        self.assertEqual(Ejercicio.objects.count(), 42)
        self.assertEqual(
            set(
                Ejercicio.objects.filter(nombre__in=nuevos)
                .values_list("nombre", flat=True)
            ),
            nuevos,
        )

        planes = {
            plan.objetivo: plan
            for plan in PlanEntrenamiento.objects.filter(activo=True)
        }
        self.assertEqual(len(planes), 4)
        for objetivo in ObjetivoChoice.values:
            plan = planes[objetivo]
            self.assertEqual(plan.fases.filter(activo=True).count(), 3)
            for fase in plan.fases.filter(activo=True):
                self.assertEqual(fase.dias.filter(activo=True).count(), 3)
                for dia in fase.dias.filter(activo=True):
                    self.assertEqual(
                        dia.ejercicios_programados.filter(activo=True).count(),
                        6,
                    )

        ejercicios_estetica = set(
            planes[ObjetivoChoice.ESTETICO]
            .fases.filter(orden=1)
            .values_list(
                "dias__ejercicios_programados__ejercicio__nombre",
                flat=True,
            )
        )
        ejercicios_salud = set(
            planes[ObjetivoChoice.SALUD]
            .fases.filter(orden=1)
            .values_list(
                "dias__ejercicios_programados__ejercicio__nombre",
                flat=True,
            )
        )
        ejercicios_perder_peso = set(
            planes[ObjetivoChoice.PERDER_PESO]
            .fases.filter(orden=1)
            .values_list(
                "dias__ejercicios_programados__ejercicio__nombre",
                flat=True,
            )
        )
        self.assertTrue(nuevos.intersection(ejercicios_estetica))
        self.assertTrue(nuevos.intersection(ejercicios_salud))
        self.assertTrue(nuevos.intersection(ejercicios_perder_peso))
        self.assertNotEqual(ejercicios_estetica, ejercicios_salud)
        self.assertNotEqual(ejercicios_estetica, ejercicios_perder_peso)
        self.assertNotEqual(ejercicios_salud, ejercicios_perder_peso)
        self.assertIn(
            "Caminata inclinada en caminadora",
            ejercicios_perder_peso,
        )
        self.assertIn(
            "Remo en máquina ergométrica",
            ejercicios_perder_peso,
        )

        call_command("cargar_plan_hipertrofia", verbosity=0)
        self.assertEqual(
            PlanEntrenamiento.objects.filter(activo=True).count(),
            4,
        )
        for plan in PlanEntrenamiento.objects.filter(activo=True):
            self.assertEqual(
                plan.fases.filter(
                    activo=True,
                    dias__activo=True,
                    dias__ejercicios_programados__activo=True,
                ).distinct().count(),
                3,
            )

    def test_perder_peso_inicia_personalizacion_sin_plan_rigido(self):
        usuario = User.objects.create_user(
            username="perder-peso@example.com",
            email="perder-peso@example.com",
            password="ClaveSegura2026!",
        )
        self.client.force_login(usuario)

        respuesta = self.client.post(
            reverse("objetivo"),
            {"objetivo": ObjetivoChoice.PERDER_PESO},
        )

        self.assertRedirects(
            respuesta,
            reverse("nivel_entrenamiento"),
            fetch_redirect_response=False,
        )
        perfil = PerfilUsuario.objects.get(user=usuario)
        self.assertEqual(
            perfil.objetivo,
            ObjetivoChoice.PERDER_PESO,
        )
        self.assertFalse(
            AsignacionPlanUsuario.objects.filter(usuario=usuario).exists()
        )

        respuesta = self.client.post(
            reverse("nivel_entrenamiento"),
            {"nivel": "principiante"},
        )
        self.assertRedirects(
            respuesta,
            reverse("configurar_rutina"),
            fetch_redirect_response=False,
        )
        respuesta = self.client.post(
            reverse("configurar_rutina"),
            {
                "dias": ["0", "2", "5"],
                "minutos": "60",
                "descanso": "75",
                "modalidad": "automatica",
            },
        )
        self.assertRedirects(
            respuesta,
            reverse("dieta"),
            fetch_redirect_response=False,
        )
        asignacion = AsignacionPlanUsuario.objects.get(
            usuario=usuario,
            estado=EstadoAsignacionChoice.ACTIVO,
        )
        self.assertTrue(asignacion.plan.es_personalizado)
        self.assertEqual(asignacion.plan.dias_por_semana, 3)
        self.assertEqual(
            list(asignacion.horarios.order_by("numero_dia_plan").values_list("dia_semana", flat=True)),
            [0, 2, 5],
        )

    def test_registro_muestra_resumen_corporal_antes_del_entrenamiento(self):
        respuesta = self.client.post(
            reverse("registrarse"),
            {
                "nombre": "Prueba",
                "apellido": "MaikerGym",
                "telefono": "3001234567",
                "direccion": "Calle de prueba 123",
                "email": "flujo@example.com",
                "password": "ClaveSegura2026!",
                "confirmar_password": "ClaveSegura2026!",
                "fecha_nacimiento": "2000-05-20",
                "tipo_documento": "CE",
                "documento": "A1234567",
            },
        )
        self.assertRedirects(
            respuesta,
            reverse("revisar_registro"),
            fetch_redirect_response=False,
        )

        usuario = User.objects.get(email="flujo@example.com")
        perfil = PerfilUsuario.objects.get(user=usuario)
        self.assertEqual(perfil.fecha_nacimiento, date(2000, 5, 20))
        self.assertEqual(perfil.telefono, "3001234567")
        self.assertEqual(perfil.direccion, "Calle de prueba 123")
        self.assertEqual(perfil.tipo_documento, "CE")
        self.assertEqual(perfil.documento, "A1234567")

        respuesta = self.client.post(
            reverse("objetivo"),
            {"objetivo": ObjetivoChoice.ESTETICO},
        )
        self.assertRedirects(
            respuesta,
            reverse("nivel_entrenamiento"),
            fetch_redirect_response=False,
        )

        respuesta = self.client.post(
            reverse("nivel_entrenamiento"),
            {"nivel": "intermedio"},
        )
        self.assertRedirects(
            respuesta,
            reverse("prueba_nivel"),
            fetch_redirect_response=False,
        )
        respuesta = self.client.post(
            reverse("prueba_nivel"),
            {clave: "2" for clave in (
                "experiencia", "frecuencia", "tecnica", "cargas",
                "progresion", "recuperacion", "compuestos", "consistencia",
            )},
        )
        self.assertRedirects(
            respuesta,
            reverse("configurar_rutina"),
            fetch_redirect_response=False,
        )
        respuesta = self.client.post(
            reverse("configurar_rutina"),
            {
                "dias": ["1", "3", "5"],
                "minutos": "75",
                "descanso": "90",
                "modalidad": "automatica",
            },
        )
        self.assertRedirects(
            respuesta,
            reverse("dieta"),
            fetch_redirect_response=False,
        )

        self.assertEqual(
            len(obtener_guia_nutricional(ObjetivoChoice.ESTETICO)["dias"]),
            7,
        )
        respuesta = self.client.post(reverse("dieta"))
        self.assertRedirects(
            respuesta,
            reverse("datos_personales"),
            fetch_redirect_response=False,
        )

        respuesta = self.client.post(
            reverse("datos_personales"),
            {
                "genero": "masculino",
                "peso": "72.50",
                "altura_cm": "175",
                "metodo_grasa": "visual:15",
            },
        )
        self.assertRedirects(
            respuesta,
            reverse("resultado_corporal"),
            fetch_redirect_response=False,
        )

        perfil.refresh_from_db()
        self.assertTrue(perfil.personalizacion_completa())
        evaluacion = perfil.evaluacion_corporal_interna()
        self.assertEqual(evaluacion['imc'], 23.67)
        self.assertEqual(evaluacion['masa_grasa_estimada_kg'], 10.9)
        self.assertEqual(evaluacion['masa_sin_grasa_estimada_kg'], 61.6)
        asignacion = AsignacionPlanUsuario.objects.get(
            usuario=usuario,
            estado=EstadoAsignacionChoice.ACTIVO,
        )
        self.assertEqual(
            asignacion.plan.objetivo,
            ObjetivoChoice.ESTETICO,
        )

        perfil.refresh_from_db()
        self.assertTrue(perfil.orientacion_nutricional_vista)
        self.assertTrue(perfil.datos_completos)
        self.assertEqual(float(perfil.porcentaje_grasa_estimado), 15.0)
        self.assertEqual(perfil.metodo_estimacion_grasa, "visual")

    def test_descanso_en_minutos_y_dias_sin_campo_de_cantidad(self):
        usuario = User.objects.create_user(
            username="dias-minutos@example.com",
            email="dias-minutos@example.com",
            password="ClaveSegura2026!",
        )
        perfil = PerfilUsuario.objects.get(user=usuario)
        perfil.objetivo = ObjetivoChoice.SALUD
        perfil.nivel_declarado = "principiante"
        perfil.nivel_entrenamiento = "principiante"
        perfil.prueba_nivel_completada = True
        perfil.genero = "femenino"
        perfil.save()
        self.client.force_login(usuario)

        respuesta = self.client.post(reverse("configurar_rutina"), {
            "dias": ["1", "6"],
            "minutos": "60",
            "descanso_valor": "5",
            "descanso_unidad": "minutos",
            "modalidad": "personalizada",
            "genero_previo": "masculino",
        })

        self.assertRedirects(respuesta, reverse("crear_rutina"), fetch_redirect_response=False)
        perfil.refresh_from_db()
        self.assertEqual(perfil.dias_entrenamiento, [1, 6])
        self.assertEqual(perfil.descanso_preferido_segundos, 300)
        self.assertEqual(perfil.genero, "femenino")

    def test_rutina_manual_exige_aviso_y_un_ejercicio_por_dia(self):
        usuario = User.objects.create_user(
            username="manual@example.com",
            email="manual@example.com",
            password="ClaveSegura2026!",
        )
        perfil = PerfilUsuario.objects.get(user=usuario)
        perfil.objetivo = ObjetivoChoice.SALUD
        perfil.nivel_declarado = "principiante"
        perfil.nivel_entrenamiento = "principiante"
        perfil.prueba_nivel_completada = True
        perfil.save()
        self.client.force_login(usuario)
        respuesta = self.client.post(reverse("configurar_rutina"), {
            "dias": ["0", "4"], "minutos": "60", "descanso": "60",
            "modalidad": "personalizada",
        })
        self.assertRedirects(respuesta, reverse("crear_rutina"), fetch_redirect_response=False)
        ejercicios = list(Ejercicio.objects.order_by("id")[:2])
        respuesta = self.client.post(reverse("crear_rutina"), {
            "acepta_aviso": "on",
            "dia": ["1", "2"],
            "ejercicio_id": [str(ejercicios[0].pk), str(ejercicios[1].pk)],
            "series": ["3", "3"],
            "cantidad": ["10", "12"],
            "descanso": ["60", "75"],
        })
        self.assertRedirects(respuesta, reverse("dieta"), fetch_redirect_response=False)
        perfil.refresh_from_db()
        self.assertTrue(perfil.aviso_rutina_personalizada_aceptado)
        pagina = self.client.get(reverse('crear_rutina'))
        self.assertEqual(len(pagina.context['filas_iniciales']), 2)
        self.assertContains(pagina, 'Ejercicios para el día lunes')
        self.assertTrue(pagina.context['editando'])
        asignacion = AsignacionPlanUsuario.objects.get(usuario=usuario, estado="activo")
        self.assertEqual(
            asignacion.plan.fases.get().dias.filter(
                ejercicios_programados__activo=True,
            ).distinct().count(),
            2,
        )

    def test_rutina_manual_persiste_y_muestra_racha_semanal_continua(self):
        """La rutina personal debe seguir siendo la activa al volver al panel."""
        usuario = User.objects.create_user(username="manual-persistente")
        perfil = PerfilUsuario.objects.get(user=usuario)
        perfil.objetivo = ObjetivoChoice.SALUD
        perfil.nivel_declarado = "principiante"
        perfil.nivel_entrenamiento = "principiante"
        perfil.prueba_nivel_completada = True
        perfil.orientacion_nutricional_vista = True
        perfil.datos_completos = True
        perfil.save()
        ejercicios = list(Ejercicio.objects.order_by("id")[:2])

        asignacion = crear_rutina_personalizada(
            usuario,
            perfil.objetivo,
            perfil.nivel_entrenamiento,
            [0, 2],
            [
                {"dia": "1", "ejercicio_id": str(ejercicios[0].pk), "series": "3", "cantidad": "10", "descanso": "60"},
                {"dia": "2", "ejercicio_id": str(ejercicios[1].pk), "series": "3", "cantidad": "10", "descanso": "60"},
            ],
        )
        perfil.refresh_from_db()
        self.assertEqual(perfil.modalidad_rutina, "personalizada")
        self.assertTrue(perfil.configuracion_entrenamiento_completa)

        # Simula una cuenta antigua que conservó una recomendación activa.
        # La rutina manual debe seguir siendo la que se muestra al usuario.
        crear_rutina_automatica(
            usuario, perfil.objetivo, perfil.nivel_entrenamiento,
            [0, 2], 60, 60,
        )
        asignacion.estado = EstadoAsignacionChoice.ACTIVO
        asignacion.save(update_fields=["estado", "fecha_actualizacion"])

        self.client.force_login(usuario)
        respuesta = self.client.get(reverse("mi_entrenamiento"))
        self.assertEqual(respuesta.context["asignacion"].pk, asignacion.pk)
        self.assertIn("Día 1 · Lunes", ' '.join(respuesta.content.decode().split()))
        self.assertContains(respuesta, "primer paso cuenta")

        dia_uno = asignacion.plan.fases.get().dias.get(numero=1)
        SesionEntrenamiento.objects.create(
            asignacion=asignacion,
            dia_plan=dia_uno,
            fecha=timezone.localdate(),
            semana_plan=asignacion.semana_actual,
            estado=EstadoSesionChoice.COMPLETADA,
        )
        respuesta = self.client.get(reverse("mi_entrenamiento"))
        self.assertContains(respuesta, "Racha de entrenamiento")
        self.assertContains(respuesta, "Día completado")

        asignacion.fecha_inicio = timezone.localdate() - timedelta(days=(998 * 7))
        asignacion.save(update_fields=["fecha_inicio", "fecha_actualizacion"])
        self.assertEqual(asignacion.semana_actual, 999)

    def test_sesion_futura_no_bloquea_edicion_ni_se_muestra_en_curso(self):
        """Una sesión con fecha futura no puede aparentar que ya empezó."""
        usuario = User.objects.create_user(username="sesion-futura")
        perfil = PerfilUsuario.objects.get(user=usuario)
        perfil.objetivo = ObjetivoChoice.SALUD
        perfil.nivel_entrenamiento = "principiante"
        perfil.prueba_nivel_completada = True
        perfil.orientacion_nutricional_vista = True
        perfil.datos_completos = True
        perfil.save()
        ejercicio = Ejercicio.objects.order_by("id").first()
        asignacion = crear_rutina_personalizada(
            usuario,
            perfil.objetivo,
            perfil.nivel_entrenamiento,
            [1, 3],
            [
                {"dia": "1", "ejercicio_id": str(ejercicio.pk), "series": "3", "cantidad": "10", "descanso": "60"},
                {"dia": "2", "ejercicio_id": str(ejercicio.pk), "series": "3", "cantidad": "10", "descanso": "60"},
            ],
        )
        dia_futuro = asignacion.plan.fases.get().dias.get(numero=2)
        SesionEntrenamiento.objects.create(
            asignacion=asignacion,
            dia_plan=dia_futuro,
            fecha=timezone.localdate() + timedelta(days=2),
            semana_plan=asignacion.semana_actual,
            estado=EstadoSesionChoice.EN_PROGRESO,
        )

        self.assertFalse(entrenamiento_en_curso(usuario))
        self.client.force_login(usuario)
        respuesta = self.client.get(reverse("mi_entrenamiento"))
        self.assertNotContains(respuesta, "Entrenamiento en curso")

    def test_nutricion_y_motivacion_tienen_contenido_suficiente(self):
        self.assertEqual(len(MENSAJES_MOTIVACIONALES), 70)
        self.assertEqual(len(set(MENSAJES_MOTIVACIONALES)), 70)
        self.assertEqual(set(NUTRICION_POR_OBJETIVO), set(ObjetivoChoice.values))
        for guia in NUTRICION_POR_OBJETIVO.values():
            self.assertEqual(len(guia["dias"]), 7)
        usuario = User.objects.create_user(
            username="motivacion@example.com",
            email="motivacion@example.com",
        )
        perfil = PerfilUsuario.objects.get(user=usuario)
        perfil.objetivo = ObjetivoChoice.HIPERTROFIA
        perfil.save(update_fields=["objetivo"])
        vistos = []
        inicio = date(2026, 9, 1)
        for desplazamiento in range(23):
            vistos.extend(
                item["mensaje"]
                for item in obtener_mensajes_del_dia(
                    usuario,
                    perfil,
                    inicio + timedelta(days=desplazamiento),
                )
            )
        self.assertEqual(len(vistos), 69)
        self.assertEqual(len(set(vistos)), 69)


class EliminacionCuentaTest(TestCase):
    def _usuario_completo_sin_datos(self, username):
        usuario = User.objects.create_user(username=username, password='Clave-segura-123!')
        perfil = PerfilUsuario.objects.get(user=usuario)
        perfil.rol = 'admin'  # Permite entrar a Mi cuenta sin el flujo de personalización.
        perfil.save(update_fields=['rol'])
        return usuario

    def test_eliminar_cuenta_transfiere_administracion_y_no_muestra_json_crudo(self):
        from .models import GrupoAmigos, IntegranteGrupo

        usuario = self._usuario_completo_sin_datos('sale-del-grupo')
        sucesor = self._usuario_completo_sin_datos('nuevo-admin')
        grupo = GrupoAmigos.objects.create(nombre='Equipo', administrador=usuario)
        IntegranteGrupo.objects.create(usuario=usuario, grupo=grupo)
        IntegranteGrupo.objects.create(usuario=sucesor, grupo=grupo)
        self.client.force_login(usuario)

        respuesta = self.client.post(reverse('cuenta'), {
            'accion': 'eliminar_cuenta',
            'password_actual': 'Clave-segura-123!',
        })

        self.assertFalse(User.objects.filter(pk=usuario.pk).exists())
        grupo.refresh_from_db()
        self.assertEqual(grupo.administrador_id, sucesor.pk)
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.url, reverse('inicio'))

    def test_contrasena_incorrecta_muestra_mensaje_en_cuenta(self):
        usuario = self._usuario_completo_sin_datos('no-se-borra')
        self.client.force_login(usuario)

        respuesta = self.client.post(reverse('cuenta'), {
            'accion': 'eliminar_cuenta',
            'password_actual': 'incorrecta',
        })

        self.assertTrue(User.objects.filter(pk=usuario.pk).exists())
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.url, reverse('cuenta'))
        self.assertIn('La contraseña no coincide', ' '.join(str(m) for m in respuesta.wsgi_request._messages))

    def test_accion_de_cuenta_ausente_no_falla_silenciosamente(self):
        usuario = self._usuario_completo_sin_datos('accion-ausente')
        self.client.force_login(usuario)

        respuesta = self.client.post(reverse('cuenta'), {
            'password_actual': 'Clave-segura-123!',
        })

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.url, reverse('cuenta'))
        self.assertIn('acción válida', ' '.join(str(m) for m in respuesta.wsgi_request._messages))

    def test_error_de_base_de_datos_no_sale_como_500_ni_borra_parcialmente(self):
        usuario = self._usuario_completo_sin_datos('fallo-al-borrar')
        self.client.force_login(usuario)

        with patch.object(User, 'delete', side_effect=IntegrityError('fallo simulado')):
            with patch('gym_project.gym_app.views.logger.exception'):
                respuesta = self.client.post(reverse('cuenta'), {
                    'accion': 'eliminar_cuenta',
                    'password_actual': 'Clave-segura-123!',
                })

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.url, reverse('cuenta'))
        self.assertTrue(User.objects.filter(pk=usuario.pk).exists())
        self.assertIn('error interno', ' '.join(str(m) for m in respuesta.wsgi_request._messages))

    def test_eliminar_cuenta_sin_sucesor_cierra_el_grupo_vacio(self):
        from .models import GrupoAmigos, IntegranteGrupo

        usuario = self._usuario_completo_sin_datos('ultimo-del-grupo')
        grupo = GrupoAmigos.objects.create(nombre='Grupo vacío al salir', administrador=usuario)
        IntegranteGrupo.objects.create(usuario=usuario, grupo=grupo)
        self.client.force_login(usuario)

        respuesta = self.client.post(reverse('cuenta'), {
            'accion': 'eliminar_cuenta',
            'password_actual': 'Clave-segura-123!',
        })

        self.assertFalse(User.objects.filter(pk=usuario.pk).exists())
        self.assertFalse(GrupoAmigos.objects.filter(pk=grupo.pk).exists())
        self.assertEqual(respuesta.url, reverse('inicio'))

    def test_eliminar_cuenta_limpia_su_plan_pero_conserva_plan_compartido(self):
        from .models import (
            AsignacionPlanUsuario,
            DiaPlan,
            FasePlan,
            PlanEntrenamiento,
        )

        usuario = self._usuario_completo_sin_datos('propietario-que-se-va')
        otro_usuario = self._usuario_completo_sin_datos('usuario-que-sigue')
        plan = PlanEntrenamiento.objects.create(
            nombre='Plan personal compartido',
            objetivo='salud',
            nivel='principiante',
            descripcion='Plan de prueba',
            propietario=usuario,
            es_personalizado=True,
        )
        fase = FasePlan.objects.create(
            plan=plan,
            nombre='Base',
            orden=1,
            semana_inicio=1,
            semana_fin=12,
        )
        dia = DiaPlan.objects.create(fase=fase, numero=1, nombre='Día 1')
        asignacion_usuario = AsignacionPlanUsuario.objects.create(usuario=usuario, plan=plan)
        AsignacionPlanUsuario.objects.create(usuario=otro_usuario, plan=plan)
        SesionEntrenamiento.objects.create(
            asignacion=asignacion_usuario,
            dia_plan=dia,
            semana_plan=1,
        )
        self.client.force_login(usuario)

        respuesta = self.client.post(reverse('cuenta'), {
            'accion': 'eliminar_cuenta',
            'password_actual': 'Clave-segura-123!',
        })

        self.assertFalse(User.objects.filter(pk=usuario.pk).exists())
        plan.refresh_from_db()
        self.assertIsNone(plan.propietario_id)
        self.assertTrue(AsignacionPlanUsuario.objects.filter(usuario=otro_usuario, plan=plan).exists())
        self.assertEqual(respuesta.url, reverse('inicio'))
