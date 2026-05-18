# beauty_shop/apps/core/urls.py
from django.urls import path
from .views import HomeView, AboutView, ContactView
# Opcionales (descomenta si las implementas)
# from .views import MaintenanceView, HealthCheckView

app_name = 'core'

urlpatterns = [
    # Página principal
    path('', HomeView.as_view(), name='home'),

    # Página "Acerca de nosotros"
    path('about/', AboutView.as_view(), name='about'),

    # Página de contacto (canónica en /contacto/, alias /contact/)
    path('contacto/', ContactView.as_view(), name='contact'),
    path('contact/', ContactView.as_view()),

    # Opcionales: mantenimiento y estado del sistema
    # path('maintenance/', MaintenanceView.as_view(), name='maintenance'),
    # path('health/', HealthCheckView.as_view(), name='health_check'),
]
