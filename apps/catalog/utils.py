from pathlib import Path
from django.utils.text import slugify

def product_image_upload_path(instance, filename):
    """
    Devuelve una ruta del tipo:
    img/<categoria>/<producto>/<archivo>
    """
    category_slug = slugify(instance.category.name) if instance.category else 'sin-categoria'
    product_slug  = slugify(instance.name)
    return Path('img') / category_slug / product_slug / filename
