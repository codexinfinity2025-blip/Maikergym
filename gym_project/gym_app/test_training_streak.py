from datetime import date, timedelta
from unittest import TestCase
from .training_streak import calcular_racha


class TrainingStreakTests(TestCase):
    def test_never_started_and_future_or_duplicate_sessions(self):
        today = date(2026, 9, 16)
        self.assertEqual(calcular_racha([], [], today, 4)['estado'], 'sin_iniciar')
        self.assertEqual(calcular_racha([today + timedelta(days=1)], [], today, 4)['semana'], 0)
        self.assertEqual(calcular_racha([today, today], [], today, 4)['dias'], 1)

    def test_rest_days_preserve_streak_but_missing_scheduled_day_breaks_it(self):
        monday = date(2026, 9, 14)
        wednesday = monday + timedelta(days=2)
        self.assertEqual(calcular_racha([monday], [monday, wednesday], wednesday, 2)['dias'], 1)
        result = calcular_racha([monday], [monday, wednesday], wednesday + timedelta(days=1), 2)
        self.assertEqual(result['estado'], 'pendiente')
        self.assertEqual(result['dias'], 1)

    def test_week_deadline_depends_on_selected_days_not_seven_elapsed_days(self):
        first = date(2026, 9, 15)  # martes; segundo día: jueves
        thursday = first + timedelta(days=2)
        friday = first + timedelta(days=3)
        self.assertEqual(calcular_racha([first], [first, thursday], thursday, 2)['estado'], 'activa')
        self.assertEqual(calcular_racha([first], [first, thursday], friday, 2)['estado'], 'pendiente')
        today = first + timedelta(days=7)
        result = calcular_racha([first, today], [first, thursday, today], today, 2)
        self.assertEqual((result['semana'], result['dia']), (1, 1))

    def test_all_week_sizes_progress_only_on_completion(self):
        first = date(2026, 9, 14)
        for size in range(1, 7):
            dates = [first + timedelta(days=i) for i in range(size + 1)]
            end = calcular_racha(dates[:size], dates, dates[size-1], size)
            self.assertTrue(end['semana_completada'])
            self.assertEqual((end['semana'], end['dia']), (1, size))
            following = calcular_racha(dates, dates, dates[-1], size)
            self.assertEqual((following['semana'], following['dia']), (2, 1))

    def test_missing_day_turns_gray_until_selected_week_closes(self):
        days = [date(2026, 9, 14) + timedelta(days=i) for i in range(3)]
        result = calcular_racha([days[0], days[2]], days, days[2], 3)
        self.assertEqual(result['estado'], 'pendiente')
        self.assertEqual(result['dias'], 2)
        after = calcular_racha([days[0], days[2]], days, days[0]+timedelta(days=7), 3)
        self.assertEqual(after['estado'], 'reiniciada')
        self.assertEqual(after['dias'], 0)

    def test_completed_week_survives_rest_and_each_incomplete_week_resets(self):
        monday = date(2026, 9, 14)
        for size in range(2, 7):
            scheduled = [monday + timedelta(days=i) for i in range(size)]
            next_day = scheduled[-1] + timedelta(days=1)
            self.assertEqual(calcular_racha(scheduled, scheduled, next_day, size)['estado'], 'activa')
            self.assertEqual(calcular_racha(scheduled[:-1], scheduled, next_day, size)['estado'], 'pendiente')
            self.assertEqual(calcular_racha(scheduled[:-1], scheduled, monday + timedelta(days=7), size)['estado'], 'reiniciada')

    def test_weekend_completed_on_sunday_counts_as_full_week(self):
        saturday = date(2026, 9, 19)
        sunday = saturday + timedelta(days=1)
        result = calcular_racha([saturday, sunday], [saturday, sunday], sunday, 2)
        self.assertTrue(result['semana_completada'])
        self.assertEqual((result['semana'], result['dia']), (1, 2))
