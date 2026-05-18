"""
sync_content - Sincroniza la estructura de carpetas content/ con la base de datos.

Convierte el directorio `content/` en la fuente unica de verdad para:
  - categorias y subcategorias (catalog.Category)
  - productos (catalog.Product) en `content/categorias/<padre>/<sub>/productos/<slug>/`
  - servicios (services.Service) en `content/categorias/servicios/<slug>/`
  - categoria de servicios (services.ServiceCategory) en `content/categorias/servicios/`

Reglas:
  - Carpeta nueva  -> registro creado
  - JSON cambiado  -> registro actualizado
  - Carpeta borrada-> registro marcado is_active=False (NO se borra)
  - El parent se infiere de la jerarquia de carpetas
  - Los errores se loggean y NO interrumpen la corrida

Uso:
  python manage.py sync_content
  python manage.py sync_content --dry-run    (solo muestra cambios, no escribe)
  python manage.py sync_content --verbose    (output detallado)

Reporte:
  Al finalizar escribe `output/sync_report.json` con creados, actualizados,
  desactivados y errores por tipo de entidad.
"""
import json
import shutil
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from apps.catalog.models import Brand, Category, Product
# Catálogo unificado: la app services fue retirada. El sincronizado de
# servicios desde content/ queda deshabilitado; los servicios ahora se
# gestionan como Product(item_type='service') vía `import_catalog`.
# Alias solo para que las anotaciones de tipo resuelvan.
ServiceCategory = Category
Service = Product


IMAGE_EXTS = ('.jpg', '.jpeg', '.png', '.webp')
SERVICES_TOP_SLUG = 'servicios'  # carpeta especial bajo content/categorias/
PRODUCTS_DIR_NAME = 'productos'  # subcarpeta esperada bajo cada subcategoria

VALID_PRICING_TYPES = {'quote', 'fixed', 'monthly', 'hourly', 'project'}


class Command(BaseCommand):
    help = "Sincroniza content/ con la base de datos (categorias, productos y servicios)."

    # ────────────────────────────────────────────────────
    #  Argumentos
    # ────────────────────────────────────────────────────
    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help='Muestra que se haria sin escribir nada en la BD.')
        parser.add_argument('--verbose', action='store_true',
                            help='Output detallado de cada cambio.')

    # ────────────────────────────────────────────────────
    #  Entrypoint
    # ────────────────────────────────────────────────────
    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.verbose = options['verbose']

        self.content_root = Path(settings.BASE_DIR) / 'content' / 'categorias'
        self.media_root = Path(settings.MEDIA_ROOT)

        if not self.content_root.exists():
            self.stderr.write(self.style.ERROR(
                f'No existe la carpeta {self.content_root}. Crea content/categorias/ primero.'
            ))
            return

        self.stdout.write(self.style.HTTP_INFO(
            f'Sincronizando desde: {self.content_root}'
        ))
        if self.dry_run:
            self.stdout.write(self.style.WARNING(
                '** DRY RUN - no se haran cambios reales en la BD **'
            ))

        # Reporte estructurado por tipo de entidad
        self.report = {
            'started_at': timezone.now().isoformat(),
            'dry_run': self.dry_run,
            'categories':       _empty_stats(),
            'products':         _empty_stats(),
            'service_category': _empty_stats(),
            'services':         _empty_stats(),
            'errors':           [],
        }

        # Slugs vistos en disco (por tipo) — para deactivar lo que ya no esta
        seen_category_slugs = set()
        seen_product_slugs = set()
        seen_service_slugs = set()
        seen_service_category_slugs = set()

        # ── Pasada 1: categorias y subcategorias ──────────────
        for category_dir in sorted(self.content_root.iterdir()):
            if not category_dir.is_dir():
                continue

            # La carpeta especial `servicios/` se procesa aparte (servicios, no Category)
            if category_dir.name == SERVICES_TOP_SLUG:
                continue

            top = self._sync_category(category_dir, parent=None)
            if not top:
                continue
            seen_category_slugs.add(top.slug)

            for child_dir in sorted(category_dir.iterdir()):
                if not child_dir.is_dir():
                    continue
                if child_dir.name == PRODUCTS_DIR_NAME:
                    continue  # productos directos bajo la categoria principal (no soportado)

                sub = self._sync_category(child_dir, parent=top)
                if not sub:
                    continue
                seen_category_slugs.add(sub.slug)

                # Productos dentro de esta subcategoria
                products_dir = child_dir / PRODUCTS_DIR_NAME
                if products_dir.is_dir():
                    for product_dir in sorted(products_dir.iterdir()):
                        if not product_dir.is_dir():
                            continue
                        prod = self._sync_product(product_dir, sub)
                        if prod:
                            seen_product_slugs.add(prod.slug)

        # ── Pasada 2: servicios ───────────────────────────────
        services_root = self.content_root / SERVICES_TOP_SLUG
        if services_root.is_dir():
            sc = self._sync_service_category(services_root)
            if sc:
                seen_service_category_slugs.add(sc.slug)
                for service_dir in sorted(services_root.iterdir()):
                    if not service_dir.is_dir():
                        continue
                    svc = self._sync_service(service_dir, sc)
                    if svc:
                        seen_service_slugs.add(svc.slug)

        # ── Pasada 3: deactivacion de huerfanos ───────────────
        self._deactivate_missing_categories(seen_category_slugs)
        self._deactivate_missing_products(seen_product_slugs)
        self._deactivate_missing_services(seen_service_slugs)
        # ServiceCategory no tiene is_active — solo se reportan huerfanos

        # ── Reporte final ─────────────────────────────────────
        self.report['finished_at'] = timezone.now().isoformat()
        self._print_report()
        self._write_report_file()

    # ────────────────────────────────────────────────────
    #  Categorias (Catalog)
    # ────────────────────────────────────────────────────
    def _sync_category(self, folder: Path, parent: Category | None) -> Category | None:
        data = self._read_data_json(folder, kind='category')
        if data is None:
            return None

        slug = data.get('slug') or slugify(folder.name)
        defaults = {
            'name': data.get('name') or folder.name.replace('-', ' ').title(),
            'description': data.get('description', ''),
            'icon': data.get('icon', ''),
            'order': _safe_int(data.get('order'), default=0),
            'is_active': bool(data.get('is_active', True)),
            'parent': parent,
            'source_path': str(folder.relative_to(settings.BASE_DIR)),
            'last_synced_at': timezone.now(),
        }

        # Imagen de portada (nombre fijo: portada.<ext>)
        cover = self._find_image(folder, basename='portada')
        defaults['image_path'] = (
            str(cover.relative_to(settings.BASE_DIR)).replace('\\', '/')
            if cover else ''
        )

        return self._upsert(
            model=Category, kind='categories', slug=slug,
            defaults=defaults, label=f'{_tag(parent)} {slug}',
            change_fields=('name', 'description', 'icon', 'order',
                           'is_active', 'parent_id', 'image_path'),
        )

    # ────────────────────────────────────────────────────
    #  Productos (Catalog)
    # ────────────────────────────────────────────────────
    def _sync_product(self, folder: Path, category: Category) -> Product | None:
        """
        Sincroniza la ESTRUCTURA del producto desde content/.
        NO toca precio ni stock — eso vive en Excel y se sincroniza con
        `sync_inventory_from_excel`. Si el JSON los trae (legacy), solo se
        usan al CREAR el producto por primera vez (bootstrap), nunca al
        actualizar uno existente.
        """
        data = self._read_data_json(folder, kind='product')
        if data is None:
            return None

        slug = data.get('slug') or slugify(folder.name)
        name = data.get('name') or folder.name.replace('-', ' ').title()

        # Resolver brand opcional por nombre
        brand_obj = None
        brand_name = (data.get('brand') or '').strip()
        if brand_name and not self.dry_run:
            brand_obj, _ = Brand.objects.get_or_create(name=brand_name)

        # Imagen principal + galeria completa (todas las imagenes del folder).
        primary_image_rel = self._stage_product_images(folder, slug, category)

        # Defaults estructurales (sin price/stock; esos vienen del Excel).
        defaults = {
            'name': name,
            'description': data.get('description', ''),
            'category': category,
            'brand': brand_obj,
            'is_active': bool(data.get('active', data.get('is_active', True))),
            'model_number': data.get('sku') or data.get('model_number') or '',
        }
        if primary_image_rel is not None:
            defaults['image'] = primary_image_rel

        # Bootstrap de price/stock SOLO si el producto no existe aun en BD
        # (asi seed_products.py sigue funcionando para datos iniciales sin
        # forzar Excel desde el dia 1).
        if not self.dry_run and not Product.objects.filter(slug=slug).exists():
            try:
                price_seed = Decimal(str(data.get('price', '0')))
            except (InvalidOperation, TypeError):
                price_seed = Decimal('0')
            defaults['price'] = price_seed
            defaults['stock'] = _safe_int(data.get('stock'), default=0)

        return self._upsert(
            model=Product, kind='products', slug=slug,
            defaults=defaults, label=f'[{category.slug}/productos] {slug}',
            change_fields=('name', 'description', 'category_id', 'brand_id',
                           'is_active', 'model_number', 'image'),
        )

    def _stage_product_images(self, folder: Path, slug: str,
                              category: Category) -> str | None:
        """
        Copia TODAS las imagenes del folder de producto a MEDIA_ROOT preservando
        el nombre de archivo (necesario para detectar color por nombre).

        Estructura destino:
          MEDIA_ROOT/inventario/img/<cat_slug>/<product_slug>/<filename>

        Retorna la ruta relativa de la imagen "primaria" (primera por orden
        alfabetico) o None si la carpeta no tiene imagenes. La galeria completa
        se descubre en runtime via Product.gallery_images().
        """
        # Listar imagenes del folder de producto (ordenadas por nombre).
        srcs = sorted(
            (c for c in folder.iterdir()
             if c.is_file() and c.suffix.lower() in IMAGE_EXTS),
            key=lambda p: p.name.lower(),
        )
        if not srcs:
            return None

        cat_slug = slugify(category.name)
        rel_dest_dir = Path('inventario') / 'img' / cat_slug / slug
        abs_dest_dir = self.media_root / rel_dest_dir

        if self.dry_run:
            primary = srcs[0]
            return str(rel_dest_dir / primary.name).replace('\\', '/')

        try:
            abs_dest_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            self._record_error(folder, f'no se pudo crear carpeta destino: {e}')
            return None

        copied = 0
        for src in srcs:
            abs_dest = abs_dest_dir / src.name
            try:
                if not abs_dest.exists() or src.stat().st_mtime > abs_dest.stat().st_mtime:
                    shutil.copy2(src, abs_dest)
                    copied += 1
            except OSError as e:
                self._record_error(folder, f'no se pudo copiar {src.name}: {e}')

        if self.verbose and copied:
            self._log(f'    -> {copied}/{len(srcs)} imagenes copiadas a {rel_dest_dir}', 'HTTP_INFO')

        # Imagen primaria = primera por orden alfabetico.
        return str(rel_dest_dir / srcs[0].name).replace('\\', '/')

    # ────────────────────────────────────────────────────
    #  ServiceCategory (apps.services)
    # ────────────────────────────────────────────────────
    def _sync_service_category(self, folder: Path) -> ServiceCategory | None:
        # Deshabilitado: catálogo unificado. Servicios se importan vía
        # `import_catalog` como Product(item_type='service').
        return None

    # ────────────────────────────────────────────────────
    #  Service (apps.services)
    # ────────────────────────────────────────────────────
    def _sync_service(self, folder: Path, category: ServiceCategory) -> Service | None:
        # Deshabilitado: catálogo unificado. Servicios se importan vía
        # `import_catalog` como Product(item_type='service').
        return None

    def _stage_service_image(self, folder: Path, slug: str) -> str | None:
        src = None
        for child in sorted(folder.iterdir()):
            if child.is_file() and child.suffix.lower() in IMAGE_EXTS:
                src = child
                break
        if src is None:
            return None

        rel_dest = Path('services') / 'img' / f'{slug}{src.suffix.lower()}'
        abs_dest = self.media_root / rel_dest

        if self.dry_run:
            return str(rel_dest).replace('\\', '/')

        try:
            abs_dest.parent.mkdir(parents=True, exist_ok=True)
            if not abs_dest.exists() or src.stat().st_mtime > abs_dest.stat().st_mtime:
                shutil.copy2(src, abs_dest)
        except OSError as e:
            self._record_error(folder, f'no se pudo copiar imagen {src.name}: {e}')
            return None

        return str(rel_dest).replace('\\', '/')

    # ────────────────────────────────────────────────────
    #  Upsert generico + deactivacion
    # ────────────────────────────────────────────────────
    def _upsert(self, *, model, kind, slug, defaults, label, change_fields):
        if self.dry_run:
            self._log(f'  [dry-run] {label}: simularia upsert', 'NOTICE')
            obj = model(slug=slug, **{k: v for k, v in defaults.items() if k != 'parent'})
            return obj

        try:
            obj, created = model.objects.update_or_create(slug=slug, defaults=defaults)
        except Exception as e:
            self._record_error_for_slug(kind, slug, str(e))
            return None

        if created:
            self.report[kind]['created'] += 1
            self._log(f'  [+] {label}: creada', 'SUCCESS')
        else:
            if self._has_meaningful_change(obj, defaults, change_fields):
                self.report[kind]['updated'] += 1
                self._log(f'  [~] {label}: actualizada', 'NOTICE')
            else:
                self.report[kind]['unchanged'] += 1
                if self.verbose:
                    self._log(f'  [=] {label}: sin cambios', 'HTTP_INFO')
        return obj

    def _has_meaningful_change(self, obj, new_values: dict, fields: tuple) -> bool:
        for field in fields:
            if field.endswith('_id'):
                base = field[:-3]
                related = new_values.get(base)
                new_val = related.id if related is not None else None
                current = getattr(obj, field, None)
            elif field == 'image':
                current_file = getattr(obj, field, None)
                current = current_file.name if current_file else ''
                new_val = new_values.get(field) or ''
            else:
                new_val = new_values.get(field)
                current = getattr(obj, field, None)

            # Normaliza None <-> '' para CharField/TextField
            if isinstance(current, str) or isinstance(new_val, str):
                current = current or ''
                new_val = new_val or ''

            # Decimal: comparar siempre como Decimal con misma escala
            if isinstance(current, Decimal) or isinstance(new_val, Decimal):
                current = Decimal(str(current)) if current is not None else None
                new_val = Decimal(str(new_val)) if new_val is not None else None

            if current != new_val:
                return True
        return False

    def _deactivate_missing_categories(self, seen: set):
        self._deactivate_missing(Category, 'categories', seen)

    def _deactivate_missing_products(self, seen: set):
        self._deactivate_missing(Product, 'products', seen)

    def _deactivate_missing_services(self, seen: set):
        # Deshabilitado: catálogo unificado (ver _sync_service). No-op para
        # NO desactivar productos por error (Service ahora es Product).
        return

    def _deactivate_missing(self, model, kind, seen: set):
        qs = model.objects.filter(is_active=True).exclude(slug__in=seen)
        if self.dry_run:
            for obj in qs:
                self._log(f'  [dry-run] {obj.slug} ({kind}): se desactivaria', 'WARNING')
            return
        count = 0
        for obj in qs:
            obj.is_active = False
            if hasattr(obj, 'last_synced_at'):
                obj.last_synced_at = timezone.now()
                obj.save(update_fields=['is_active', 'last_synced_at'])
            else:
                obj.save(update_fields=['is_active'])
            self._log(f'  [-] {obj.slug} ({kind}): desactivada', 'WARNING')
            count += 1
        self.report[kind]['deactivated'] = count

    # ────────────────────────────────────────────────────
    #  IO helpers
    # ────────────────────────────────────────────────────
    def _read_data_json(self, folder: Path, *, kind: str) -> dict | None:
        data_file = folder / 'data.json'
        if not data_file.exists():
            self._log(f'  [skip] {folder.name}: sin data.json', 'WARNING')
            return None
        try:
            return json.loads(data_file.read_text(encoding='utf-8'))
        except json.JSONDecodeError as e:
            self._record_error(folder, f'data.json invalido ({e})')
            return None
        except OSError as e:
            self._record_error(folder, f'no se pudo leer data.json ({e})')
            return None

    def _find_image(self, folder: Path, *, basename: str) -> Path | None:
        for ext in IMAGE_EXTS:
            p = folder / f'{basename}{ext}'
            if p.exists():
                return p
        return None

    # ────────────────────────────────────────────────────
    #  Logging y reporte
    # ────────────────────────────────────────────────────
    def _log(self, msg, style='HTTP_INFO'):
        styler = getattr(self.style, style, self.style.HTTP_INFO)
        self.stdout.write(styler(msg))

    def _record_error(self, folder: Path, msg: str):
        rel = str(folder.relative_to(settings.BASE_DIR))
        full = f'{rel}: {msg}'
        self.report['errors'].append({'path': rel, 'message': msg})
        self.stderr.write(self.style.ERROR(f'  [error] {full}'))

    def _record_error_for_slug(self, kind: str, slug: str, msg: str):
        full = f'{kind}/{slug}: {msg}'
        self.report['errors'].append({'kind': kind, 'slug': slug, 'message': msg})
        self.stderr.write(self.style.ERROR(f'  [error] {full}'))

    def _print_report(self):
        s = self.report
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('=' * 60))
        self.stdout.write(self.style.HTTP_INFO('  Reporte de sincronizacion'))
        self.stdout.write(self.style.HTTP_INFO('=' * 60))
        for kind in ('categories', 'products', 'service_category', 'services'):
            st = s[kind]
            self.stdout.write(
                f'  {kind:18s}  +{st["created"]:<3d} ~{st["updated"]:<3d} '
                f'={st["unchanged"]:<3d} -{st["deactivated"]:<3d}'
            )
        if s['errors']:
            self.stdout.write(self.style.ERROR(f'  Errores: {len(s["errors"])}'))
        self.stdout.write(self.style.HTTP_INFO('=' * 60))
        if self.dry_run:
            self.stdout.write(self.style.WARNING(
                '  ** DRY RUN - ningun cambio fue persistido **'
            ))

    def _write_report_file(self):
        out_dir = Path(settings.BASE_DIR) / 'output'
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / 'sync_report.json'
            out_path.write_text(
                json.dumps(self.report, indent=2, ensure_ascii=False, default=str),
                encoding='utf-8',
            )
            self.stdout.write(self.style.HTTP_INFO(f'  Reporte: {out_path}'))
        except OSError as e:
            self.stderr.write(self.style.ERROR(f'No se pudo escribir el reporte: {e}'))


# ────────────────────────────────────────────────────
#  Helpers de modulo
# ────────────────────────────────────────────────────
def _empty_stats() -> dict:
    return {'created': 0, 'updated': 0, 'unchanged': 0, 'deactivated': 0}


def _safe_int(value, *, default: int = 0) -> int:
    try:
        return int(value) if value is not None else default
    except (TypeError, ValueError):
        return default


def _tag(parent):
    return f'[{parent.slug}/]' if parent else '[ROOT]   '
