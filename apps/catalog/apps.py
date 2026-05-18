from django.apps import AppConfig


class CatalogConfig(AppConfig):
    name = 'apps.catalog'
    verbose_name = 'Catalogo'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        # Importa signals para que se registren al arrancar la app
        import apps.catalog.signals  # noqa: F401
