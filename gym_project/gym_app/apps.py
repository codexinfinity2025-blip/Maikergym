from django.apps import AppConfig

class GymAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gym_project.gym_app'
    verbose_name = 'Aplicación Gym'

    def ready(self):
        import gym_project.gym_app.signals
