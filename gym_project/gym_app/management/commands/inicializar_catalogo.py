from django.core.management import BaseCommand, CommandError, call_command
from django.db import transaction
from gym_project.gym_app.models import Ejercicio, PlanEntrenamiento


class Command(BaseCommand):
    help = 'Carga inicial explícita en una base vacía; no modifica catálogos existentes.'

    @transaction.atomic
    def handle(self, *args, **options):
        if Ejercicio.objects.exists() or PlanEntrenamiento.objects.exists():
            raise CommandError('El catálogo ya contiene datos. No se modificó ningún ejercicio ni plan.')
        call_command('cargar_ejercicios', stdout=self.stdout)
        call_command('cargar_plan_hipertrofia', stdout=self.stdout)
