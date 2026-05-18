from django.apps import AppConfig


class CartConfig(AppConfig):
    name = 'apps.cart'
    verbose_name = 'Carrito'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        import apps.cart.signals  # noqa: F401
