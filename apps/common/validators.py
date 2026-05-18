# beauty_shop\apps\common\validators.py
import os
from django.core.exceptions import ValidationError


def validate_file_extension(allowed_extensions=None):
    """
    Retorna un validador para extensiones de archivos.

    Uso:
        image = models.FileField(validators=[validate_file_extension(['jpg', 'png'])])
    """
    allowed_extensions = allowed_extensions or ['jpg', 'jpeg', 'png']

    def validator(value):
        ext = os.path.splitext(value.name)[1][1:].lower()
        if ext not in allowed_extensions:
            raise ValidationError(f"Extensión no permitida: .{ext}. Solo se permiten: {', '.join(allowed_extensions)}")

    return validator


def validate_file_size(max_size_mb=5):
    """
    Validador para tamaño máximo de archivos en MB.

    Uso:
        image = models.FileField(validators=[validate_file_size(2)])  # máx 2 MB
    """
    def validator(value):
        limit = max_size_mb * 1024 * 1024
        if value.size > limit:
            raise ValidationError(f"El archivo es demasiado grande. Máximo permitido: {max_size_mb} MB.")
    return validator
