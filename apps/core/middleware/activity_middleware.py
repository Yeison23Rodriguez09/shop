# beauty_shop\apps\core\middleware\activity_middleware.py
import datetime
from django.utils.timezone import now


class UpdateLastActivityMiddleware:
    """
    Middleware para actualizar el campo `last_activity` del usuario autenticado.
    Útil para saber quién está activo y cuándo fue su última acción.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Solo actualiza si el usuario está autenticado
        if request.user.is_authenticated:
            last_activity = request.session.get('last_activity')
            now_time = now()

            # Evita actualizar en cada request: solo si pasaron más de 60 segundos
            if not last_activity or (now_time - datetime.datetime.fromisoformat(last_activity)).seconds > 60:
                request.user.last_activity = now_time
                request.user.save(update_fields=['last_activity'])
                request.session['last_activity'] = now_time.isoformat()

        response = self.get_response(request)
        return response
