from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from gym_project.gym_app.models import PerfilUsuario

@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if kwargs.get('raw'):
        return
    if created:
        PerfilUsuario.objects.create(user=instance, activo=instance.is_active)
    elif getattr(instance, '_cambio_activo', False):
        PerfilUsuario.objects.filter(user_id=instance.pk).update(activo=instance.is_active)


@receiver(pre_save, sender=User)
@receiver(pre_save, sender=PerfilUsuario)
def detectar_cambio_activo(sender, instance, update_fields=None, raw=False, **kwargs):
    campo = 'is_active' if sender is User else 'activo'
    instance._cambio_activo = False
    if raw or not instance.pk or (update_fields is not None and campo not in update_fields):
        return
    anterior = sender.objects.filter(pk=instance.pk).values_list(campo, flat=True).first()
    instance._cambio_activo = anterior is not None and anterior != getattr(instance, campo)


@receiver(post_save, sender=PerfilUsuario)
def sincronizar_estado_usuario(sender, instance, raw=False, **kwargs):
    if not raw and getattr(instance, '_cambio_activo', False):
        User.objects.filter(pk=instance.user_id).update(is_active=instance.activo)
