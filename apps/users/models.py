# apps/users/models.py
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils.translation import gettext_lazy as _
from .managers import CustomUserManager


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        CUSTOMER = 'customer', _('Cliente')
        ADMIN = 'admin', _('Administrador')

    email = models.EmailField(_('Correo electrónico'), unique=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER,
        verbose_name=_('Rol')
    )

    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        related_name="customuser_groups",
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('user permissions'),
        blank=True,
        related_name="customuser_permissions",
        related_query_name="user",
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email


# ═══════════════════════════════════════════════════════════
#  Perfil extendido del usuario
# ═══════════════════════════════════════════════════════════
class UserProfile(models.Model):
    """
    Información adicional del cliente: datos de contacto y dirección principal.
    Se crea automáticamente al registrar un nuevo usuario (via signal).
    """
    TIPO_DOC_CHOICES = [
        ('CC',  'Cédula de Ciudadanía'),
        ('CE',  'Cédula de Extranjería'),
        ('NIT', 'NIT (empresa)'),
        ('PP',  'Pasaporte'),
    ]

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Usuario',
    )

    # Contacto
    phone = models.CharField('Teléfono / WhatsApp', max_length=20, blank=True)
    tipo_documento = models.CharField(
        'Tipo de documento', max_length=5,
        choices=TIPO_DOC_CHOICES, default='CC', blank=True
    )
    numero_documento = models.CharField('Número de documento', max_length=30, blank=True)

    # Dirección principal
    address_line1 = models.CharField('Dirección', max_length=200, blank=True,
                                     help_text='Ej: Calle 45 # 12-30, Apto 301')
    address_line2 = models.CharField('Barrio / Conjunto', max_length=100, blank=True)
    city = models.CharField('Ciudad', max_length=100, blank=True)
    department = models.CharField('Departamento', max_length=100, blank=True)
    postal_code = models.CharField('Código postal', max_length=10, blank=True)

    # Empresa (opcional — clientes corporativos)
    company_name = models.CharField('Empresa', max_length=150, blank=True)
    company_nit = models.CharField('NIT empresa', max_length=30, blank=True)

    # Meta
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Perfil de usuario'
        verbose_name_plural = 'Perfiles de usuario'

    def __str__(self):
        return f'Perfil de {self.user.email}'

    @property
    def full_address(self):
        parts = [self.address_line1, self.address_line2, self.city, self.department]
        return ', '.join(p for p in parts if p)
