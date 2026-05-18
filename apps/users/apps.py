from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = 'apps.users'
    verbose_name = 'Usuarios'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        import apps.users.signals  # noqa: F401
