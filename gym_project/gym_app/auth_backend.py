from django.contrib.auth.backends import ModelBackend


class ActiveProfileBackend(ModelBackend):
    """Bloquea tanto nuevos accesos como sesiones existentes de perfiles inactivos."""
    def user_can_authenticate(self, user):
        from .models import PerfilUsuario
        return super().user_can_authenticate(user) and not PerfilUsuario.objects.filter(
            user_id=user.pk, activo=False,
        ).exists()
