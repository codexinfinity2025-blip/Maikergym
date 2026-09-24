from datetime import date, timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.http import HttpResponse
from django.urls import reverse

from .models import AsignacionPlanUsuario, DiaPlan, HorarioPlanUsuario
from .services import _crear_plan_vacio, iniciar_sesion_entrenamiento
from .training_streak import obtener_racha


class FlexibleScheduleTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='flexible')
        plan, fase = _crear_plan_vacio(self.user, 'salud', 'principiante', 2, 'Flexible')
        self.assignment = AsignacionPlanUsuario.objects.create(
            usuario=self.user, plan=plan, fecha_inicio=date(2026, 9, 14), estado='activo')
        self.days = []
        for numero, weekday in enumerate([1, 2], 1):
            day = DiaPlan.objects.create(fase=fase, numero=numero, nombre=f'Sesión {numero}')
            HorarioPlanUsuario.objects.create(asignacion=self.assignment, numero_dia_plan=numero, dia_semana=weekday)
            self.days.append(day)

    def start(self, day, today, planned=None):
        with patch('gym_project.gym_app.services.timezone.localdate', return_value=today):
            return iniciar_sesion_entrenamiento(self.assignment, day, fecha_programada=planned)

    def test_makeup_counts_for_original_day_without_duplicate_session(self):
        today = date(2026, 9, 16)
        planned = today - timedelta(days=1)
        session, created = self.start(self.days[0], today, planned)
        self.assertTrue(created)
        self.assertEqual((session.fecha, session.fecha_programada), (today, planned))
        same, created = self.start(self.days[0], today, planned)
        self.assertFalse(created)
        self.assertEqual(same.pk, session.pk)
        session.estado = 'completada'
        session.save(update_fields=['estado'])
        result = obtener_racha(self.assignment, today, list(self.assignment.horarios.all()))
        self.assertEqual(result['dias'], 1)
        self.assertEqual(result['estado'], 'activa')
        with self.assertRaises(ValidationError):
            self.start(self.days[1], today)

    def test_can_choose_normal_wednesday_without_replacing_tuesday(self):
        session, _ = self.start(self.days[1], date(2026, 9, 16))
        self.assertEqual(session.dia_plan_id, self.days[1].pk)
        self.assertEqual(session.fecha_programada, date(2026, 9, 16))

    def test_can_make_up_on_rest_day(self):
        session, _ = self.start(self.days[0], date(2026, 9, 19), date(2026, 9, 15))
        self.assertEqual(session.fecha.weekday(), 5)
        self.assertEqual(session.fecha_programada.weekday(), 1)

    def test_rejects_future_previous_week_and_wrong_weekday(self):
        today = date(2026, 9, 16)
        for planned in [date(2026, 9, 17), date(2026, 9, 8), date(2026, 9, 14)]:
            with self.subTest(planned=planned), self.assertRaises(ValidationError):
                self.start(self.days[0], today, planned)

    def test_weekend_only_supports_both_days(self):
        for horario, weekday in zip(self.assignment.horarios.order_by('numero_dia_plan'), [5, 6]):
            horario.dia_semana = weekday
            horario.save(update_fields=['dia_semana'])
        for day, today in zip(self.days, [date(2026, 9, 19), date(2026, 9, 20)]):
            session, _ = self.start(day, today)
            session.estado = 'completada'
            session.save(update_fields=['estado'])
        result = obtener_racha(self.assignment, date(2026, 9, 20), list(self.assignment.horarios.all()))
        self.assertTrue(result['semana_completada'])
        self.assertEqual((result['semana'], result['dia']), (1, 2))

    def test_configuration_saves_weekend_choice_and_rejects_quantity_mismatch(self):
        self.client.force_login(self.user)
        data = {'dias': ['5', '6'], 'cantidad_dias': '2', 'minutos': '60',
                'descanso': '60', 'modalidad': 'personalizada', 'enfoque_corporal': 'full_body'}
        with patch('gym_project.gym_app.views.siguiente_paso_personalizacion', return_value='configurar_rutina'):
            response = self.client.post(reverse('configurar_rutina'), data)
            self.assertEqual(response.status_code, 302)
            from .models import PerfilUsuario
            self.assertEqual(PerfilUsuario.objects.get(user=self.user).dias_entrenamiento, [5, 6])
            data['cantidad_dias'] = '3'
            with patch('gym_project.gym_app.views.render', return_value=HttpResponse()) as render:
                self.client.post(reverse('configurar_rutina'), data)
                self.assertIn('exactamente', render.call_args.args[2]['error'])

    def test_social_completion_credits_makeup_to_original_date(self):
        from .models import DiaComprometido
        from .social_services import resumen_usuario
        planned = date(2026, 9, 15)
        today = date(2026, 9, 19)
        DiaComprometido.objects.create(usuario=self.user, fecha=planned)
        session, _ = self.start(self.days[0], today, planned)
        session.estado = 'completada'
        session.save(update_fields=['estado'])
        with patch('gym_project.gym_app.social_services.timezone.localdate', return_value=today):
            self.assertEqual(resumen_usuario(self.user)['cumplidos'], 1)
