# beauty_shop/apps/common/utils.py
import uuid
from django.utils.text import slugify
from django.utils.timezone import now


def generate_unique_slug(model_class, value: str, slug_field_name: str = 'slug') -> str:
    """
    Genera un slug único para un modelo, evitando colisiones.

    Args:
        model_class: Clase del modelo a verificar.
        value: Texto base para generar el slug.
        slug_field_name: Campo que se usa como slug (por defecto 'slug').

    Returns:
        str: Un slug único.
    """
    base_slug = slugify(value)
    unique_slug = base_slug
    num = 1

    while model_class.objects.filter(**{slug_field_name: unique_slug}).exists():
        unique_slug = f"{base_slug}-{num}"
        num += 1

    return unique_slug


def generate_order_code(prefix: str = 'ORD') -> str:
    """
    Genera un código de orden único con un prefijo.

    Returns:
        str: Código como 'ORD-1A2B3C4D'.
    """
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def timestamped_filename(instance, filename: str) -> str:
    """
    Genera un nombre único para archivos subidos, basado en el timestamp y el modelo.

    Args:
        instance: Instancia del modelo que sube el archivo.
        filename: Nombre original del archivo.

    Returns:
        str: Nombre de archivo con timestamp, dentro de una carpeta con el nombre del modelo.
    """
    ext = filename.split('.')[-1]
    name_slug = slugify(str(instance))
    timestamp = now().strftime('%Y%m%d%H%M%S')
    new_filename = f"{name_slug}-{timestamp}.{ext}"
    folder = instance.__class__.__name__.lower()
    return f"{folder}/{new_filename}"
