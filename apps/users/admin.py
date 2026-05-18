# apps/users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import CustomUser, UserProfile


class UserProfileInline(admin.StackedInline):
    """Permite editar el perfil directamente desde la ficha del usuario."""
    model = UserProfile
    can_delete = False
    extra = 0
    fk_name = 'user'
    fieldsets = (
        ('Contacto', {
            'fields': ('phone', 'tipo_documento', 'numero_documento')
        }),
        ('Dirección', {
            'fields': (
                'address_line1', 'address_line2',
                'city', 'department', 'postal_code',
            )
        }),
        ('Empresa (opcional)', {
            'fields': ('company_name', 'company_nit'),
            'classes': ('collapse',),
        }),
    )


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    """Admin del usuario extendido con email como identificador."""
    list_display = ('email', 'username', 'first_name', 'last_name',
                    'role', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        (_('Datos personales'), {
            'fields': ('first_name', 'last_name', 'role')
        }),
        (_('Permisos'), {
            'fields': ('is_active', 'is_staff', 'is_superuser',
                       'groups', 'user_permissions'),
        }),
        (_('Fechas importantes'), {
            'fields': ('last_login', 'date_joined'),
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2',
                       'first_name', 'last_name', 'role'),
        }),
    )

    inlines = [UserProfileInline]


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """También se puede gestionar el perfil de manera independiente."""
    list_display = ('user', 'phone', 'city', 'department', 'company_name')
    search_fields = ('user__email', 'phone', 'city', 'company_name')
    list_filter = ('department', 'tipo_documento')
    autocomplete_fields = ('user',)
