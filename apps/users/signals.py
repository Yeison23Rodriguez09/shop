# apps/users/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Crea automáticamente el perfil extendido y asigna grupo por defecto
    cada vez que se registra un nuevo usuario.
    """
    if created:
        # Importación tardía para evitar circular imports
        from apps.users.models import UserProfile
        UserProfile.objects.get_or_create(user=instance)

        # Asignar grupo por defecto
        if instance.role == User.Role.CUSTOMER:
            group_name = 'Clientes'
        elif instance.role == User.Role.ADMIN:
            group_name = 'Administradores'
        else:
            group_name = None

        if group_name:
            group, _ = Group.objects.get_or_create(name=group_name)
            instance.groups.add(group)
