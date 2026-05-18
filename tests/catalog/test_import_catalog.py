"""
Tests del catálogo unificado:

  - test_import_catalog_from_excel  : importa productos/servicios desde .xlsx
  - test_import_with_clear_flag     : --clear borra lo viejo antes de importar
  - test_service_and_product_in_catalog : /shop/ lista ambos + filtro ?tipo=
  - test_whatsapp_number_updated    : el número WhatsApp está actualizado
"""
import pytest
import openpyxl
from decimal import Decimal

from django.core.management import call_command
from django.urls import reverse

from apps.catalog.models import Category, Product


HEADERS = ['Nombre', 'Descripción', 'Precio', 'Stock',
           'Categoría', 'Tipo', 'Imagen', 'Especificaciones']


def _make_xlsx(path, rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(HEADERS)
    for r in rows:
        ws.append(r)
    wb.save(path)
    return str(path)


# ─── 1. Importación desde Excel ───────────────────────────────────────────────

@pytest.mark.django_db
def test_import_catalog_from_excel(tmp_path):
    xlsx = _make_xlsx(tmp_path / 'cat.xlsx', [
        ['Cámara IP 4MP', 'Domo 4MP', 350000, 12, 'CCTV', 'Producto', '',
         '{"resolución": "4MP"}'],
        ['Instalación CCTV', 'Montaje profesional', 0, 0, 'Instalación',
         'Servicio', '', '{"garantía": "90 días"}'],
    ])

    call_command('import_catalog', file=xlsx)

    assert Product.objects.count() == 2

    cam = Product.objects.get(slug='camara-ip-4mp')
    assert cam.item_type == 'product'
    assert cam.price == Decimal('350000')
    assert cam.stock == 12
    assert cam.category.name == 'CCTV'
    assert cam.specs_dict.get('resolución') == '4MP'

    svc = Product.objects.get(slug='instalacion-cctv')
    assert svc.item_type == 'service'
    assert svc.is_service is True
    assert svc.price == Decimal('0')


# ─── 2. Flag --clear ──────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_import_with_clear_flag(tmp_path):
    vieja = Category.objects.create(name='Vieja', slug='vieja')
    Product.objects.create(
        name='Producto Viejo', slug='producto-viejo',
        price=Decimal('1000'), stock=1, category=vieja,
    )
    assert Product.objects.count() == 1

    xlsx = _make_xlsx(tmp_path / 'c.xlsx', [
        ['Producto Nuevo', 'Nuevo', 99000, 5, 'CCTV', 'Producto', '', ''],
    ])
    call_command('import_catalog', file=xlsx, clear=True)

    assert Product.objects.count() == 1
    assert not Product.objects.filter(slug='producto-viejo').exists()
    assert Product.objects.filter(slug='producto-nuevo').exists()


# ─── 3. Producto + servicio en el catálogo unificado ──────────────────────────

@pytest.mark.django_db
def test_service_and_product_in_catalog(client):
    cat = Category.objects.create(name='CCTV', slug='cctv', is_active=True)
    Product.objects.create(
        name='Cámara Bullet', slug='camara-bullet', item_type='product',
        price=Decimal('250000'), stock=10, category=cat, is_active=True,
    )
    Product.objects.create(
        name='Servicio Mantenimiento', slug='servicio-mantenimiento',
        item_type='service', price=Decimal('0'), stock=0,
        category=cat, is_active=True,
    )

    url = reverse('catalog:product_list')

    def _names(resp):
        # Se valida sobre el queryset de la vista (no el HTML completo:
        # los servicios también aparecen en el menú global del navbar).
        return sorted(p.name for p in resp.context['products'])

    # Sin filtro: ambos en la lista unificada
    r = client.get(url)
    assert r.status_code == 200
    assert _names(r) == ['Cámara Bullet', 'Servicio Mantenimiento']

    # ?tipo=service: solo el servicio
    r = client.get(url, {'tipo': 'service'})
    assert _names(r) == ['Servicio Mantenimiento']

    # ?tipo=product: solo el producto
    r = client.get(url, {'tipo': 'product'})
    assert _names(r) == ['Cámara Bullet']


# ─── 4. Búsqueda ?q= ──────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_search_query_filters(client):
    cat = Category.objects.create(name='CCTV', slug='cctv', is_active=True)
    Product.objects.create(
        name='Cámara CCTV Exterior', slug='camara-cctv-exterior',
        item_type='product', price=Decimal('300000'), stock=5,
        category=cat, is_active=True,
    )
    Product.objects.create(
        name='Alarma Inalámbrica', slug='alarma-inalambrica',
        item_type='product', price=Decimal('200000'), stock=5,
        description='Kit de alarma', category=cat, is_active=True,
    )
    url = reverse('catalog:product_list')

    r = client.get(url, {'q': 'cctv'})
    names = sorted(p.name for p in r.context['products'])
    assert names == ['Cámara CCTV Exterior']

    r = client.get(url, {'q': 'alarma'})
    names = sorted(p.name for p in r.context['products'])
    assert names == ['Alarma Inalámbrica']

    # Búsqueda + filtro de tipo combinados
    r = client.get(url, {'q': 'a', 'tipo': 'product'})
    assert all(p.item_type == 'product' for p in r.context['products'])


# ─── 5. specifications es JSONField (dict) ────────────────────────────────────

@pytest.mark.django_db
def test_specifications_is_jsonfield():
    from django.db.models import JSONField
    field = Product._meta.get_field('specifications')
    assert isinstance(field, JSONField), 'specifications debe ser JSONField'

    cat = Category.objects.create(name='Cat', slug='cat')
    p = Product.objects.create(
        name='Servicio X', slug='servicio-x', item_type='service',
        price=Decimal('0'), category=cat,
        specifications={'cobertura': '24/7', 'sla': 4},
    )
    p.refresh_from_db()
    assert isinstance(p.specifications, dict)
    assert p.specifications['cobertura'] == '24/7'
    assert p.specs_dict == {'cobertura': '24/7', 'sla': 4}

    # default=dict: si no se pasa, queda {}
    p2 = Product.objects.create(
        name='Producto Y', slug='producto-y',
        price=Decimal('1000'), category=cat,
    )
    p2.refresh_from_db()
    assert p2.specifications == {}


# ─── 6. Número WhatsApp actualizado ───────────────────────────────────────────

@pytest.mark.django_db
def test_whatsapp_number_updated(client):
    r = client.get(reverse('core:home'))
    assert r.status_code == 200
    assert b'573114879338' in r.content, 'El número WhatsApp nuevo debe estar presente'
    assert b'573000000000' not in r.content, 'No debe quedar el número viejo'
