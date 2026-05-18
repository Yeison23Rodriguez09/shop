"""
Importación del catálogo unificado (productos + servicios) desde Excel.

Lee un archivo .xlsx cuya primera fila son los encabezados:

  Nombre | Descripción | Precio | Stock | Categoría | Tipo | Imagen | Especificaciones

  - Nombre          (texto, obligatorio)
  - Descripción     (texto)
  - Precio          (decimal; 0 o vacío = "A cotizar" para servicios)
  - Stock           (entero)
  - Categoría       (texto; se crea si no existe)
  - Tipo            ("Producto" o "Servicio"; default Producto)
  - Imagen          (ruta relativa a MEDIA_ROOT o URL; opcional)
  - Especificaciones(texto JSON; ej: {"resolución":"4K"})

Uso:
  python manage.py import_catalog --file catalogo.xlsx
  python manage.py import_catalog --file catalogo.xlsx --clear
  python manage.py import_catalog --file catalogo.xlsx --preview

Opciones:
  --file     Ruta al .xlsx (default: catalogo.xlsx en BASE_DIR).
  --clear    Borra TODOS los productos/servicios antes de importar.
  --preview  Muestra lo que se importaría SIN escribir en la BD.

Idempotente: usa update_or_create por slug (slugify del nombre).
"""
import json
import unicodedata
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from apps.catalog.models import Category, Product


# ── Normalización de encabezados (case/acentos-insensible) ──────────────────
def _norm(text) -> str:
    if text is None:
        return ''
    s = str(text).strip().lower()
    s = ''.join(c for c in unicodedata.normalize('NFKD', s)
                if not unicodedata.combining(c))
    return s


# Encabezado normalizado → campo lógico
HEADER_MAP = {
    'nombre': 'name',
    'descripcion': 'description',
    'precio': 'price',
    'stock': 'stock',
    'categoria': 'category',
    'subcategoria': 'subcategory',
    'tipo': 'item_type',
    'imagen': 'image_url',
    'imagen_url': 'image_url',
    'imagenurl': 'image_url',
    'image_url': 'image_url',
    'especificaciones': 'specifications',
}

TIPO_MAP = {
    'producto': 'product', 'product': 'product',
    'servicio': 'service', 'service': 'service',
}


class Command(BaseCommand):
    help = 'Importa el catálogo unificado (productos + servicios) desde un Excel.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file', default='catalogo.xlsx',
            help='Ruta al archivo .xlsx (default: catalogo.xlsx en la raíz).',
        )
        parser.add_argument(
            '--clear', action='store_true', default=False,
            help='Borra todos los productos/servicios antes de importar.',
        )
        parser.add_argument(
            '--preview', action='store_true', default=False,
            help='Muestra lo que se importaría sin guardar nada.',
        )

    # ──────────────────────────────────────────────────────────────────
    def handle(self, *args, **options):
        try:
            import openpyxl  # noqa: WPS433  (dependencia opcional)
        except ImportError:
            raise CommandError(
                'Falta la librería openpyxl. Instálala con: pip install openpyxl'
            )

        file_arg = Path(options['file'])
        path = file_arg if file_arg.is_absolute() else Path(settings.BASE_DIR) / file_arg
        if not path.exists():
            raise CommandError(f'No se encontró el archivo: {path}')

        clear = options['clear']
        preview = options['preview']

        if preview:
            self.stdout.write(self.style.WARNING('\n[PREVIEW] No se guardara nada.\n'))

        wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
        ws = wb.active

        rows = ws.iter_rows(values_only=True)
        try:
            header_row = next(rows)
        except StopIteration:
            raise CommandError('El archivo Excel está vacío (sin encabezados).')

        # Mapa columna-índice → campo lógico
        col_to_field = {}
        for idx, raw in enumerate(header_row):
            key = HEADER_MAP.get(_norm(raw))
            if key:
                col_to_field[idx] = key

        if 'name' not in col_to_field.values():
            raise CommandError(
                'Falta la columna obligatoria "Nombre". '
                f'Encabezados detectados: {list(header_row)}'
            )

        # ── --clear ───────────────────────────────────────────────────
        # Los productos referenciados por pedidos (OrderItem, on_delete=PROTECT)
        # NO pueden borrarse sin romper el histórico de órdenes: esos se
        # DESACTIVAN; el resto se elimina de verdad.
        if clear and not preview:
            from apps.orders.models import OrderItem
            ref_ids = set(OrderItem.objects.values_list('product_id', flat=True))
            borrables = Product.objects.exclude(id__in=ref_ids)
            n_del = borrables.count()
            borrables.delete()  # ProductVariant cae en cascada
            n_deact = Product.objects.filter(id__in=ref_ids).update(is_active=False)
            self.stdout.write(self.style.WARNING(
                f'  --clear: {n_del} eliminados, {n_deact} desactivados '
                f'(referenciados por pedidos).'
            ))
        elif clear and preview:
            self.stdout.write(self.style.WARNING(
                f'  --clear (preview): se limpiarían {Product.objects.count()} registros.'
            ))

        creados = actualizados = errores = 0
        self.stdout.write(self.style.HTTP_INFO('\n-- IMPORTANDO CATALOGO --------------------'))

        for n, row in enumerate(rows, start=2):  # fila 1 = encabezados
            data = {}
            for idx, field in col_to_field.items():
                data[field] = row[idx] if idx < len(row) else None

            nombre = (str(data.get('name') or '')).strip()
            if not nombre:
                continue  # fila vacía → se ignora

            try:
                resultado = self._import_row(data, nombre, preview)
                if resultado == 'CREADO':
                    creados += 1
                elif resultado == 'ACTUALIZADO':
                    actualizados += 1
                self.stdout.write(self.style.SUCCESS(f'  OK  {resultado:11s} -> {nombre}'))
            except Exception as e:  # noqa: BLE001 — reporta y continua
                errores += 1
                self.stdout.write(self.style.ERROR(f'  X   fila {n}: {nombre or "?"} - {e}'))

        wb.close()

        # ── Resumen ───────────────────────────────────────────────────
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 46))
        self.stdout.write(self.style.SUCCESS('  IMPORTACIÓN COMPLETADA'))
        self.stdout.write(self.style.SUCCESS('=' * 46))
        self.stdout.write(f'  Creados      : {creados}')
        self.stdout.write(f'  Actualizados : {actualizados}')
        if errores:
            self.stdout.write(self.style.ERROR(f'  Errores      : {errores}'))
        if preview:
            self.stdout.write(self.style.WARNING('  PREVIEW: nada fue guardado.'))
        self.stdout.write(self.style.SUCCESS('=' * 46))

    # ──────────────────────────────────────────────────────────────────
    def _import_row(self, data: dict, nombre: str, preview: bool) -> str:
        # Tipo
        item_type = TIPO_MAP.get(_norm(data.get('item_type')), 'product')

        # Precio
        price = self._to_decimal(data.get('price'))

        # Stock — acepta enteros, floats de Excel (10.0) y "ilimitado"/"" → 0
        raw_stock = data.get('stock')
        try:
            stock = int(float(raw_stock)) if raw_stock not in (None, '') else 0
        except (TypeError, ValueError):
            stock = 0  # p.ej. "ilimitado" (servicios)

        # Especificaciones → dict (JSONField). Acepta JSON string o vacío.
        raw_specs = data.get('specifications')
        specs = {}
        if isinstance(raw_specs, dict):
            specs = raw_specs
        elif raw_specs not in (None, '') and str(raw_specs).strip():
            try:
                parsed = json.loads(str(raw_specs).strip())
                specs = parsed if isinstance(parsed, dict) else {}
                if not isinstance(parsed, dict):
                    raise ValueError('no es objeto JSON')
            except (ValueError, TypeError):
                specs = {}
                self.stdout.write(self.style.WARNING(
                    f'    (aviso) Especificaciones no son JSON valido en "{nombre}" -> {{}}.'
                ))

        slug = slugify(nombre)[:220]

        if preview:
            existe = Product.objects.filter(slug=slug).exists()
            return 'ACTUALIZADO' if existe else 'CREADO'

        categoria = self._get_or_create_category(data.get('category'))

        subcat = str(data.get('subcategory') or '').strip()
        if subcat in ('-', '—', 'n/a', 'na'):
            subcat = ''

        # Imagen: si es URL http(s) → image_url (NO se descarga).
        imagen = str(data.get('image_url') or '').strip()
        es_url = imagen.lower().startswith(('http://', 'https://'))
        image_url = imagen if es_url else ''

        defaults = {
            'name': nombre,
            'item_type': item_type,
            'subcategory': subcat,
            'description': str(data.get('description') or '').strip(),
            'price': price,
            'stock': stock,
            'specifications': specs,
            'category': categoria,
            'image_url': image_url,
            'is_active': True,
        }

        with transaction.atomic():
            obj, created = Product.objects.update_or_create(
                slug=slug, defaults=defaults,
            )
            # Ruta relativa (sin http) → ImageField local opcional.
            if imagen and not es_url:
                obj.image = imagen
                obj.save(update_fields=['image'])

        return 'CREADO' if created else 'ACTUALIZADO'

    # ── Helpers ───────────────────────────────────────────────────────
    def _to_decimal(self, value) -> Decimal:
        if value in (None, ''):
            return Decimal('0')
        try:
            return Decimal(str(value).replace(',', '').strip())
        except (InvalidOperation, TypeError, ValueError):
            return Decimal('0')

    def _get_or_create_category(self, raw_name) -> Category:
        name = (str(raw_name or '')).strip() or 'General'
        slug = slugify(name)[:120]
        cat, _ = Category.objects.get_or_create(
            slug=slug,
            defaults={'name': name, 'is_active': True},
        )
        return cat
