# beauty_shop\apps\users\managers.py
from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    """
    Manager personalizado para el modelo CustomUser que utiliza email como identificador único.
    """

    def create_user(self, email, username, password=None, **extra_fields):
        """
        Crea y guarda un usuario con email y contraseña.
        """
        if not email:
            raise ValueError(_('El email debe ser proporcionado'))
        if not username:
            raise ValueError(_('El nombre de usuario debe ser proporcionado'))

        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        """
        Crea y guarda un superusuario con email y contraseña.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('El superusuario debe tener is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('El superusuario debe tener is_superuser=True.'))

        return self.create_user(email, username, password, **extra_fields)
