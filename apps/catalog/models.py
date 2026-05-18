# securityshop/apps/catalog/models.py
from django.db import models
from django.utils.text import slugify
import os


# 🖼️ Ruta dinámica: inventario/img/categoria/producto/imagen.jpg
def product_image_upload_path(instance, filename):
    categoria = slugify(instance.category.name)
    producto = slugify(instance.name)
    return f'inventario/img/{categoria}/{producto}/{filename}'


# 📂 Categoría de producto de seguridad electrónica
# Soporta jerarquía: una categoría puede tener un parent (categoría padre).
# Si parent es None → es categoría principal (CCTV, Alarmas, etc.)
# Si parent NO es None → es subcategoría (Cámaras IP, Sensores de movimiento, etc.)
class Category(models.Model):
    name = models.CharField("Nombre", max_length=100)
    slug = models.SlugField("Slug", max_length=120, unique=True, blank=True)
    description = models.CharField("Descripción corta", max_length=255, blank=True)
    icon = models.CharField(
        "Ícono (clase CSS, ej: fa-camera)",
        max_length=80,
        blank=True,
        help_text="Clase de Font Awesome o similar. Ej: fa-camera-security"
    )

    # ── Jerarquía ─────────────────────────────────────
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='children',
        null=True, blank=True,
        verbose_name='Categoría padre',
        help_text='Si está vacío, es categoría principal. Si tiene valor, es subcategoría.'
    )

    # ── Visualización y orden ─────────────────────────
    order = models.PositiveIntegerField(
        'Orden',
        default=0,
        help_text='Orden de aparición en menús y listados.'
    )
    image_path = models.CharField(
        'Ruta de imagen',
        max_length=255,
        blank=True,
        help_text='Ruta relativa a la imagen de portada (ej: cctv/portada.jpg).'
    )
    is_active = models.BooleanField(
        'Activa',
        default=True,
        help_text='Si está desactivada, no se muestra al cliente.'
    )

    # ── Sincronización con sistema de carpetas ────────
    source_path = models.CharField(
        'Ruta en disco',
        max_length=500,
        blank=True,
        help_text='Ruta en content/ que originó esta categoría (auto-llenada por sync_content).'
    )
    last_synced_at = models.DateTimeField(
        'Última sincronización',
        null=True, blank=True,
        help_text='Timestamp de la última vez que sync_content actualizó este registro.'
    )

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['parent__name', 'order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        if self.parent:
            return f'{self.parent.name} → {self.name}'
        return self.name

    @property
    def is_root(self):
        """True si es categoría principal (sin padre)."""
        return self.parent_id is None

    @property
    def has_children(self):
        return self.children.filter(is_active=True).exists()

    @property
    def full_path(self):
        """Ruta completa: 'CCTV / Cámaras IP'."""
        if self.parent:
            return f'{self.parent.full_path} / {self.name}'
        return self.name


# 🏷️ Marca
class Brand(models.Model):
    name = models.CharField("Nombre", max_length=100, unique=True)
    country = models.CharField("País de origen", max_length=80, blank=True)
    website = models.URLField("Sitio web", blank=True)
    logo = models.ImageField("Logo", upload_to='brands/logos/', blank=True, null=True)

    class Meta:
        verbose_name = "Marca"
        verbose_name_plural = "Marcas"
        ordering = ['name']

    def __str__(self):
        return self.name


# 🛡️ Producto o servicio de seguridad electrónica (catálogo unificado)
# item_type distingue un producto físico de un servicio. Una sola lista
# en /shop/ los muestra a ambos con filtro por tipo (?tipo=product|service).
class Product(models.Model):
    ITEM_TYPE_CHOICES = [
        ('product', 'Producto'),
        ('service', 'Servicio'),
    ]

    # ── Campos base ──────────────────────────────────────────────
    item_type = models.CharField(
        "Tipo", max_length=10, choices=ITEM_TYPE_CHOICES, default='product',
        db_index=True,
        help_text="Producto físico (con stock) o servicio (instalación, monitoreo, etc.)."
    )
    name = models.CharField("Nombre", max_length=200)
    slug = models.SlugField("Slug", max_length=220, unique=True, blank=True)
    subcategory = models.CharField(
        "Subcategoría", max_length=120, blank=True,
        help_text="Subcategoría opcional dentro de la categoría "
                  "(ej: CCTV dentro de Instalaciones)."
    )
    description = models.TextField("Descripción", blank=True)
    price = models.DecimalField("Precio", max_digits=10, decimal_places=2, default=0)
    stock = models.PositiveIntegerField("Stock", default=0)
    specifications = models.JSONField(
        "Especificaciones", default=dict, blank=True,
        help_text='Especificaciones técnicas (dict JSON). '
                  'Ej: {"resolución": "4K", "garantía": "12 meses"}'
    )
    image = models.ImageField("Imagen principal", upload_to=product_image_upload_path, blank=True, null=True)
    image_url = models.URLField(
        "URL de imagen", max_length=500, blank=True, null=True,
        help_text="Imagen externa por URL (alternativa a subir un archivo)."
    )
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE,
        related_name='products', verbose_name="Categoría"
    )
    brand = models.ForeignKey(
        Brand, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='products', verbose_name="Marca"
    )
    is_active = models.BooleanField("Activo", default=True)
    created_at = models.DateTimeField("Fecha de creación", auto_now_add=True)

    # ── Campos técnicos de seguridad electrónica ──────────────────
    model_number = models.CharField(
        "Modelo / Referencia", max_length=100, blank=True,
        help_text="Código del fabricante. Ej: DS-2CD2143G2-I"
    )
    warranty_months = models.PositiveIntegerField(
        "Garantía (meses)", default=12,
        help_text="Período de garantía oficial del fabricante."
    )
    resolution = models.CharField(
        "Resolución", max_length=50, blank=True,
        help_text="Ej: 4MP, 8MP, 4K, 1080p"
    )
    connectivity = models.CharField(
        "Conectividad", max_length=100, blank=True,
        help_text="Ej: IP/PoE, WiFi, 4G, Analógico, RS-485"
    )
    power_supply = models.CharField(
        "Alimentación eléctrica", max_length=80, blank=True,
        help_text="Ej: 12V DC, PoE 802.3af, 110-220V AC"
    )
    datasheet_url = models.URLField(
        "Ficha técnica (URL)", blank=True,
        help_text="Enlace al PDF oficial del fabricante."
    )
    is_featured = models.BooleanField(
        "Destacado en inicio", default=False,
        help_text="Aparece en la sección destacada del home."
    )
    requires_installation = models.BooleanField(
        "Requiere instalación profesional", default=False,
        help_text="Indica si el producto necesita instalación técnica."
    )
    compatible_with = models.ManyToManyField(
        'self',
        blank=True,
        verbose_name="Compatible con",
        symmetrical=False,
        related_name='compatible_products',
        help_text="Otros productos compatibles o complementarios."
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Producto"
        verbose_name_plural = "Productos"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def is_service(self):
        return self.item_type == 'service'

    @property
    def get_image(self):
        """Imagen subida (ImageField) o, en su defecto, URL externa."""
        if self.image:
            try:
                return self.image.url
            except ValueError:
                pass
        if self.image_url:
            return self.image_url
        return None

    @property
    def specs_dict(self):
        """Especificaciones como dict. specifications es JSONField; toleramos
        que un registro antiguo tenga string JSON o un valor no-dict."""
        data = self.specifications
        if isinstance(data, dict):
            return data
        if isinstance(data, str) and data.strip():
            import json
            try:
                parsed = json.loads(data)
                return parsed if isinstance(parsed, dict) else {}
            except (ValueError, TypeError):
                return {}
        return {}

    @property
    def warranty_label(self):
        """Retorna la garantía en formato legible."""
        if self.warranty_months >= 12:
            years = self.warranty_months // 12
            return f"{years} año{'s' if years > 1 else ''}"
        return f"{self.warranty_months} mes{'es' if self.warranty_months > 1 else ''}"

    # ── Galeria de imagenes (descubierta del filesystem) ────
    @property
    def gallery_dir(self):
        """Ruta absoluta donde sync_content copia todas las imagenes del producto."""
        from django.conf import settings
        from django.utils.text import slugify
        cat_slug = slugify(self.category.name) if self.category_id else 'misc'
        return os.path.join(settings.MEDIA_ROOT, 'inventario', 'img', cat_slug, self.slug)

    @property
    def gallery_relative_dir(self):
        from django.utils.text import slugify
        cat_slug = slugify(self.category.name) if self.category_id else 'misc'
        return f'inventario/img/{cat_slug}/{self.slug}'

    def gallery_images(self):
        """
        Lista TODAS las imagenes del producto ordenadas por nombre de archivo.
        Retorna lista de rutas relativas al MEDIA_URL (str), ej:
        'inventario/img/<cat>/<slug>/azul_01.jpg'.
        """
        d = self.gallery_dir
        if not os.path.isdir(d):
            return []
        valid = ('.jpg', '.jpeg', '.png', '.webp', '.gif')
        files = sorted(f for f in os.listdir(d)
                       if f.lower().endswith(valid) and os.path.isfile(os.path.join(d, f)))
        prefix = self.gallery_relative_dir
        return [f'{prefix}/{f}' for f in files]

    def images_for_color(self, color):
        """
        Imagenes cuyo nombre de archivo (case-insensitive) contenga `color`.
        Si el color es vacio o no hay coincidencias, retorna toda la galeria.
        """
        all_images = self.gallery_images()
        if not color:
            return all_images
        c = color.strip().lower()
        matches = [p for p in all_images if c in os.path.basename(p).lower()]
        return matches or all_images


# 🎨 Variante de producto (color con su propio precio/stock)
# Convive con Product.price/Product.stock: si un producto NO tiene variantes,
# se usa el campo legacy del Product (default variant). Si tiene variantes,
# la UI obliga a elegir una y el inventario vive en la variante.
class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE,
        related_name='variants', verbose_name='Producto',
    )
    sku = models.CharField('SKU', max_length=80, unique=True)
    color = models.CharField(
        'Color', max_length=60, blank=True,
        help_text='Etiqueta visible (ej: rojo, azul). Tambien usada para '
                  'matchear imagenes por nombre de archivo.',
    )
    name = models.CharField(
        'Nombre visible', max_length=200, blank=True,
        help_text='Si esta vacio, se muestra "<producto> - <color>".',
    )
    price = models.DecimalField('Precio', max_digits=12, decimal_places=2, default=0)
    stock = models.PositiveIntegerField('Stock', default=0)
    is_active = models.BooleanField('Activo', default=True)

    created_at = models.DateTimeField('Creado el', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado el', auto_now=True)

    class Meta:
        ordering = ['product', 'color']
        verbose_name = 'Variante de producto'
        verbose_name_plural = 'Variantes de producto'
        unique_together = ('product', 'color')

    def __str__(self):
        return f'{self.product.name} — {self.color or "default"} ({self.sku})'

    @property
    def display_name(self):
        return self.name or f'{self.product.name} — {self.color}' if self.color else self.product.name
