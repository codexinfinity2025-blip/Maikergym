from itertools import combinations

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.template.loader import render_to_string
from django.test import SimpleTestCase, TestCase

from .models import PlanEntrenamiento, ObjetivoChoice, NivelEjercicioChoice, Ejercicio
from .routine_basis import VERSION, ZONAS, distribuir_enfoques, resumen_frecuencia
from .services import crear_rutina_automatica, crear_rutina_personalizada, _segundos_estimados


class CalendarioFundamentadoTest(SimpleTestCase):
    def test_todas_las_combinaciones_incluyen_ambas_zonas_y_respetan_recuperacion(self):
        for cantidad in range(1, 7):
            for dias in combinations(range(7), cantidad):
                for preferencia in ('superior', 'inferior', 'full_body'):
                    enfoques = distribuir_enfoques(dias, preferencia)
                    self.assertEqual(len(enfoques), cantidad)
                    self.assertEqual(set().union(*(ZONAS[e] for e in enfoques)), {'superior', 'inferior'})
                    for i, j in combinations(range(cantidad), 2):
                        if (dias[j] - dias[i]) % 7 in (1, 6):
                            self.assertFalse(ZONAS[enfoques[i]] & ZONAS[enfoques[j]])

    def test_horarios_y_advertencias(self):
        self.assertEqual(distribuir_enfoques([0, 2, 4]), ['cuerpo_completo'] * 3)
        finde = distribuir_enfoques([5, 6])
        self.assertEqual(set(finde), {'tren_superior', 'tren_inferior'})
        self.assertIn('no permite', resumen_frecuencia(finde))
        self.assertNotIn('no permite', resumen_frecuencia(distribuir_enfoques([0, 3])))


class GeneradorFundamentadoTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('cargar_ejercicios', verbosity=0)

    def setUp(self):
        self.user = User.objects.create_user(username='fundamento')

    def test_objetivos_niveles_tiempo_y_marca(self):
        for objetivo in ObjetivoChoice.values:
            for nivel in NivelEjercicioChoice.values:
                assignment = crear_rutina_automatica(self.user, objetivo, nivel, [4, 0, 2], 45, 15)
                self.assertIn(VERSION, assignment.plan.descripcion)
                self.assertEqual(list(assignment.horarios.order_by('numero_dia_plan').values_list('dia_semana', flat=True)), [0, 2, 4])
                for day in assignment.plan.fases.get().dias.all():
                    programs = list(day.ejercicios_programados.select_related('ejercicio'))
                    names = {p.ejercicio.nombre for p in programs}
                    self.assertIn('Sentadilla goblet con mancuerna', names)
                    self.assertIn('Press de pecho sentado en máquina', names)
                    self.assertIn('Remo sentado en polea', names)
                    self.assertTrue({'Puente de glúteos en suelo', 'Peso muerto rumano con barra'} & names)
                    self.assertLessEqual(len(programs), 6)
                    seconds = 600
                    for p in programs:
                        self.assertLessEqual(p.series, 3)
                        self.assertGreaterEqual(p.descanso_segundos, 120)
                        seconds += _segundos_estimados(dict(series=p.series, descanso_segundos=p.descanso_segundos,
                            duracion_segundos=p.duracion_segundos, distancia_metros=p.distancia_metros or 0,
                            repeticiones_max=p.repeticiones_max or 0))
                    self.assertLessEqual(seconds, 45 * 60)

    def test_catalogo_incompleto_no_crea_plan_y_conserva_activo(self):
        old = crear_rutina_automatica(self.user, 'salud', 'principiante', [0, 3], 60, 120)
        count = PlanEntrenamiento.objects.count()
        Ejercicio.objects.filter(nombre__in=['Remo sentado en polea', 'Jalón al pecho en polea']).update(activo=False)
        with self.assertRaises(ValidationError):
            crear_rutina_automatica(self.user, 'salud', 'principiante', [0, 3], 60, 120)
        old.refresh_from_db()
        self.assertEqual(old.estado, 'activo')
        self.assertEqual(PlanEntrenamiento.objects.count(), count)

    def test_personal_no_se_etiqueta_ni_se_reescribe(self):
        exercise = Ejercicio.objects.filter(activo=True).first()
        personal = crear_rutina_personalizada(self.user, 'salud', 'principiante', [0],
            [dict(dia=1, ejercicio_id=exercise.pk, cantidad=10, series=2, descanso=60)])
        self.assertNotIn(VERSION, personal.plan.descripcion)
        html = render_to_string('partials/routine_basis.html', {'asignacion': personal})
        self.assertIn('Tu rutina guardada se conserva', html)
        self.assertEqual(personal.plan.fases.get().dias.get().ejercicios_programados.get().descanso_segundos, 60)

    def test_fuentes_visibles_sin_aval(self):
        assignment = crear_rutina_automatica(self.user, 'salud', 'principiante', [5, 6], 60, 120)
        html = render_to_string('partials/routine_basis.html', {'asignacion': assignment})
        self.assertIn(VERSION, html)
        self.assertIn('no permite dos exposiciones', html)
        self.assertIn('PMC12965823', html)
        self.assertIn('validación profesional', html)
