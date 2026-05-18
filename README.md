# Nexo YR Secure — Plataforma E-commerce

Tienda online de **seguridad electrónica** construida con **Django 5.2** (Python 3.11).

### Objetivo comercial

Vitrina y tienda orientada a **conversión**: presentar el catálogo de equipos
(CCTV, alarmas, control de acceso, redes, domótica, energía de respaldo) y los
servicios técnicos (instalación, monitoreo, mantenimiento, soporte), y llevar al
visitante de forma clara hacia **comprar** (carrito → checkout → pago) o
**solicitar una cotización** (formulario de contacto / WhatsApp).

Diseñada para crecer: catálogo desacoplado del inventario, variantes por
color/SKU, y múltiples pasarelas de pago colombianas.

> **Estado actual:** funcional. `manage.py check` sin issues, sin migraciones
> pendientes, **148 tests en verde**, y todas las rutas comerciales responden
> (landing, catálogo, servicios, detalle, carrito, checkout, contacto, auth).
> Ver [§16 Cambios recientes](#16-cambios-recientes-auditoría) y
> [§17 Riesgos residuales](#17-riesgos-y-limitaciones-residuales).

---

## Tabla de contenido

1. [Arquitectura general](#1-arquitectura-general)
2. [Estructura de archivos](#2-estructura-de-archivos)
3. [Navegación del sitio y secciones](#3-navegación-del-sitio-y-secciones)
4. [Arranque rápido](#4-arranque-rápido)
5. [Variables de entorno](#5-variables-de-entorno)
6. [Sistema de catálogo e inventario](#6-sistema-de-catálogo-e-inventario)
7. [Gestión de imágenes y variantes de color](#7-gestión-de-imágenes-y-variantes-de-color)
8. [Formato del Excel de inventario](#8-formato-del-excel-de-inventario)
9. [Flujo de carrito y pedidos](#9-flujo-de-carrito-y-pedidos)
10. [Pasarelas de pago](#10-pasarelas-de-pago)
11. [Comandos de gestión](#11-comandos-de-gestión)
12. [Tests](#12-tests)
13. [Despliegue a producción](#13-despliegue-a-producción)
14. [Mantenimiento día a día](#14-mantenimiento-día-a-día)
15. [Convenciones y estilo](#15-convenciones-y-estilo)
16. [Cambios recientes (auditoría)](#16-cambios-recientes-auditoría)
17. [Riesgos y limitaciones residuales](#17-riesgos-y-limitaciones-residuales)

---

## 1. Arquitectura general

```
Fuente de verdad estructural          Fuente de verdad de precios/stock
        |                                        |
  content/ (carpetas                    catalogo.xlsx (Excel
  + data.json + imagenes)               por hojas de categoria)
        |                                        |
        v                                        v
  sync_content            <--- DB --->  sync_inventory_from_excel
  (crea/actualiza                       (crea/actualiza ProductVariant)
   Category + Product)
        |
        v
  media/inventario/img/<cat>/<slug>/
  (imagenes copiadas; nombre de archivo
   determina el color del variant)
```

### Flujo de una compra

```
Cliente -> ProductDetailView -> AddToCartView -> CheckoutAddressView -> CheckoutPaymentView
                                    |                   |                      |
                              CartService          (dirección)        OrderService.create_from_cart
                              (sesion / DB)                            (select_for_update -> stock)
                                                                              |
                                                                  PaymentGateway (Wompi/PayU/MP)
                                                                  o transferencia / contraentrega
                                                                              |
                                                                  Webhook -> confirm_payment
                                                                              |
                                                                  Order.status = 'paid'
```

### Capas de la aplicación

| Capa | Responsabilidad | Ubicación |
|------|----------------|-----------|
| Modelos | Persistencia y reglas de datos | `apps/*/models.py` |
| Servicios | Lógica de negocio reutilizable | `apps/*/services/` |
| Vistas | Orquestación HTTP (delegan a servicios) | `apps/*/views.py` |
| Templates | Presentación desacoplada | `templates/` |
| Context processors | Datos globales (categorías, carrito, datos del comercio) | `apps/common/context_processors.py` |
| Comandos de gestión | Operaciones batch | `apps/*/management/commands/` |

### Apps Django

| App | Propósito | Modelos |
|-----|-----------|---------|
| `apps.core` | Landing comercial, *Acerca de*, formulario de contacto | — (sin modelos) |
| `apps.catalog` | Catálogo unificado: productos **y** servicios (`Product.item_type`) | `Category`, `Brand`, `Product`, `ProductVariant` |
| `apps.cart` | Carrito híbrido sesión + BD | `CartItem` |
| `apps.orders` | Pedidos, checkout y ciclo de vida | `Order`, `OrderItem`, `OrderLog` |
| `apps.payments` | Pasarelas Wompi / PayU / MercadoPago (+ módulos Stripe/PayPal) | — (sin modelos) |
| `apps.users` | Usuario personalizado (login por email) + perfil | `CustomUser`, `Profile` |
| `apps.common` | Context processors, constantes, validadores, mixins | — (no es app instalada; utilidades) |

> **Servicios = productos:** no existe una app `services` separada. Un servicio
> es un `Product` con `item_type='service'`; el catálogo `/shop/` los muestra a
> ambos con filtro por tipo (`?tipo=product|service`).

---

## 2. Estructura de archivos

```
shop/
├── apps/                          # Aplicaciones Django
│   ├── core/                      # Landing, contacto, "acerca de"
│   ├── catalog/                   # Product, Category, Brand, ProductVariant
│   │   ├── management/commands/
│   │   │   ├── sync_content.py               # content/ -> DB
│   │   │   ├── import_catalog.py             # importación de catálogo
│   │   │   ├── sync_inventory_from_excel.py  # Excel -> ProductVariant
│   │   │   └── export_inventory_to_excel.py  # DB -> Excel (round-trip)
│   │   ├── models.py
│   │   ├── services/
│   │   └── views.py
│   ├── cart/                      # Carrito hibrido sesion + DB
│   │   └── services.py            # CartService (add/remove/merge/validate)
│   ├── orders/                    # Pedidos y ciclo de vida
│   │   ├── management/commands/cancel_expired_orders.py
│   │   └── services/order_service.py   # Stock atomico, idempotencia
│   ├── payments/                  # wompi.py, payu.py, mercadopago.py (services/)
│   │   │                          # + stripe.py / paypal.py (módulos, sin ruta aún)
│   ├── users/                     # Usuario personalizado (email-only) + perfil
│   └── common/                    # context_processors, constants, validators
│
├── config/
│   ├── urls.py                    # URLconf raíz
│   ├── settings/
│   │   ├── base.py                # Comun a todos los entornos
│   │   ├── development.py         # SQLite, DEBUG=True, email consola
│   │   └── production.py          # PostgreSQL, HTTPS, WhiteNoise, HSTS
│   ├── celery.py / wsgi.py / asgi.py / logging.py
│
├── content/categorias/            # FUENTE DE VERDAD del catalogo
│   └── <raiz>/<sub>/<producto>/
│       └── data.json              # nombre, precio, stock, descripcion...
│
├── catalogo.xlsx                  # Excel de inventario (precios/stock/variantes)
│
├── requirements/
│   ├── base.txt                   # Dependencias de runtime
│   ├── dev.txt                    # base + pytest, black, flake8
│   └── prod.txt                   # base (despliegue)
├── requirements.txt               # → apunta a requirements/dev.txt (dev local)
│
├── tests/                         # Suite pytest (148 tests)
│   └── test_shop_e2e.py           # Test E2E de los flujos críticos
│
├── conftest.py                    # Fixtures globales de pytest
├── pyproject.toml                 # black, isort, pytest, coverage
├── Makefile                       # Atajos de desarrollo
├── Procfile                       # Render / Heroku
├── render.yaml                    # Render.com (infra como codigo)
├── Dockerfile + Dockerfile.prod
└── docker-compose.yml + docker-compose.prod.yml
```

---

## 3. Navegación del sitio y secciones

El URLconf raíz es `config/urls.py`. Mapa de rutas público:

| Ruta | Vista / app | Sección |
|------|-------------|---------|
| `/` | `core.HomeView` | **Landing** comercial (hero, CTAs, features, destacados) |
| `/about/` | `core.AboutView` | Acerca de la empresa |
| `/contacto/` (alias `/contact/`) | `core.ContactView` | **Contacto / cotización** (GET form, POST envía email) |
| `/shop/` | `catalog.ProductListView` | **Catálogo** unificado (productos + servicios) |
| `/shop/?tipo=product` | `catalog.ProductListView` | Solo **productos** |
| `/shop/?tipo=service` | `catalog.ProductListView` | Solo **servicios** |
| `/shop/categoria/<slug>/` | `catalog.ProductListView` | Catálogo filtrado por categoría |
| `/shop/producto/<slug>/` | `catalog.ProductDetailView` | Detalle de producto/servicio (PDP) |
| `/productos/` | redirect 302 → `/shop/` | Alias retrocompatible |
| `/carrito/` | `cart.CartDetailView` | Carrito |
| `/carrito/add/<id>/` | `cart.AddToCartView` | Agregar al carrito (POST) |
| `/pedidos/` | `orders.OrderListView` | Mis pedidos (requiere login) |
| `/pedidos/checkout/direccion/` | `orders.CheckoutAddressView` | Checkout paso 1 — dirección |
| `/pedidos/checkout/pago/` | `orders.CheckoutPaymentView` | Checkout paso 2 — pago |
| `/pedidos/<pk>/confirmacion/` | `orders.OrderConfirmationView` | Confirmación de pedido |
| `/pagos/wompi/<order_id>/` … | `payments.*RedirectView` | Redirección a pasarela |
| `/cuentas/register/` `/cuentas/login/` … | `users.*` | Registro / login / perfil |
| `/accounts/...` | `allauth` | Auth por email (login, signup, reset) |
| `/admin/` | Django admin | Backoffice |

### Secciones principales

- **Landing (`/`)** — `templates/core/home.html`. Hero con propuesta de valor y
  dos CTAs (catálogo / contacto), 6 *feature boxes* que enlazan a servicios y
  productos, grilla de **destacados** dinámica (ítems activos con imagen) y CTA
  final "Solicitar cotización". Navbar y footer (en `base.html`) exponen el
  árbol de categorías de productos y servicios vía context processors.
- **Productos (`/shop/?tipo=product`)** — listado paginado (12/pág.), filtros
  por categoría, tipo y búsqueda de texto. Tarjetas con imagen, precio y enlace
  a la PDP.
- **Servicios (`/shop/?tipo=service`)** — misma vista, `item_type='service'`.
  Los servicios no se agregan al carrito: el flujo es **cotización vía
  contacto/WhatsApp** (precio "A cotizar" cuando `price == 0`).
- **Contacto (`/contacto/`)** — `templates/core/contact.html`. Formulario
  (nombre, email, mensaje) que envía un correo a `CONTACT_EMAIL`
  (= variable de entorno `SHOP_CONTACT_EMAIL`). Botón flotante de WhatsApp
  presente en todas las páginas.

---

## 4. Arranque rápido

### Opción A — Local con SQLite (más rápido)

```bash
# 1. Clonar
git clone <repo-url> shop && cd shop

# 2. Entorno virtual
python -m venv .venv
source .venv/bin/activate      # Linux/Mac
.venv\Scripts\activate         # Windows

# 3. Dependencias de desarrollo
pip install -r requirements.txt          # = requirements/dev.txt

# 4. Variables de entorno
cp .env.example .env
# SQLite funciona sin cambiar nada por defecto

# 5. Migraciones + admin
python manage.py migrate
python manage.py createsuperuser

# 6. Cargar catalogo de ejemplo
python manage.py sync_content
python manage.py loaddata fixtures/brands.json

# 7. Servidor
python manage.py runserver
# -> http://localhost:8000
# -> http://localhost:8000/admin
```

### Opción B — Docker Compose con PostgreSQL

```bash
cp .env.example .env
docker compose up --build

# En otro terminal (primera vez):
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py sync_content
```

### Makefile (atajos)

```bash
make install          # pip install requirements/dev.txt
make run              # python manage.py runserver
make migrate          # python manage.py migrate
make test             # pytest
make sync-content     # sync_content
make format           # black + isort
make lint             # flake8
```

---

## 5. Variables de entorno

Copia `.env.example` como `.env`. Las críticas en producción:

| Variable | Obligatoria en prod | Descripción |
|----------|---------------------|-------------|
| `SECRET_KEY` | Sí | Clave secreta Django |
| `DJANGO_SETTINGS_MODULE` | Sí | `config.settings.production` |
| `DJANGO_ENV` | Sí | `production` (lo usa `manage.py`) |
| `DATABASE_URL` | Sí | `postgres://user:pass@host:5432/db` |
| `DJANGO_ALLOWED_HOSTS` | Sí | Dominio real, coma-separado |
| `CSRF_TRUSTED_ORIGINS` | Sí | `https://tudominio.com` |
| `EMAIL_HOST_USER` | Sí | Cuenta SMTP |
| `EMAIL_HOST_PASSWORD` | Sí | App-password SMTP |
| `DEFAULT_FROM_EMAIL` | Recomendado | Remitente de los correos salientes |
| `SHOP_CONTACT_EMAIL` | **Recomendado** | Bandeja que recibe el formulario de contacto / cotizaciones |
| `SHOP_NAME`, `SHOP_CONTACT_PHONE` | Recomendado | Datos del comercio mostrados en el sitio |
| `SECURE_SSL_REDIRECT` | Recomendado | `True` en produccion |

> **La app no arranca en produccion** si `SECRET_KEY` o las credenciales de
> email no estan definidas. Fail-fast intencional.
>
> **Conversión:** `SHOP_CONTACT_EMAIL` define a dónde llegan los leads del
> formulario de contacto. Si no se configura, cae a `DEFAULT_FROM_EMAIL`.
> Configúrala con un buzón real **antes de lanzar** o se perderán cotizaciones.

---

## 6. Sistema de catálogo e inventario

### Dos fuentes de verdad, separadas

`content/` define **qué existe** (categorías, productos, descripciones, imágenes).
El **Excel** (`catalogo.xlsx`) define **cuánto cuesta y cuánto hay** (precios,
stock, variantes/SKUs).

Esta separación permite actualizar precios masivamente con un Excel sin tocar la
BD, y modificar descripciones/imágenes sin afectar el inventario.

### Comando sync_content

```bash
python manage.py sync_content
```

- Lee `content/categorias/<raiz>/<sub>/<producto>/data.json`
- Crea/actualiza `Category`, `Product`, `Brand`
- Copia imágenes a `media/inventario/img/<categoria>/<slug>/`
- **No sobreescribe** precio/stock si el producto ya existe (el Excel manda)
- Idempotente: puede ejecutarse N veces

### Formato de `data.json`

```json
{
  "name": "Camara IP 4MP",
  "price": 350000,
  "stock": 10,
  "description": "Descripcion del producto.",
  "brand": "Hikvision",
  "sku": "CAM-IP-4MP-001",
  "model_number": "DS-2CD1143G2-I",
  "warranty_months": 12,
  "requires_installation": false
}
```

---

## 7. Gestión de imágenes y variantes de color

Las imágenes viven en:
```
media/inventario/img/<categoria-slug>/<producto-slug>/
```

### Convención de nombres para variantes de color

El sistema filtra imágenes por el **nombre del archivo** — sin BD, sin
configuración extra.

| Archivo | Color detectado |
|---------|-----------------|
| `negro_01.jpg` | negro |
| `rojo_02.jpg` | rojo |
| `blanco_frente.jpg` | blanco |
| `camara_principal.jpg` | genérica (todas las variantes) |

Al seleccionar una variante en la PDP, el JS filtra las miniaturas buscando el
nombre del color (case-insensitive) en el nombre del archivo.

---

## 8. Formato del Excel de inventario

### Estructura

- Una **hoja por categoría raíz** (ej: "CCTV", "Control de Acceso")
- Columnas:

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `sku` | texto | ID único de la variante |
| `product_slug` | texto | Slug del producto en BD |
| `nombre` | texto | Nombre de la variante |
| `color` | texto | Color (vacío si no aplica) |
| `precio` | número | Precio en COP |
| `stock` | entero | Unidades disponibles |
| `activo` | `true`/`false` | Visible en tienda |

### Importar / exportar

```bash
# Importar (create-or-update por SKU, idempotente)
python manage.py sync_inventory_from_excel catalogo.xlsx

# Exportar estado actual (round-trip compatible)
python manage.py export_inventory_to_excel media/exports/snapshot.xlsx

# Con variantes inactivas
python manage.py export_inventory_to_excel snapshot.xlsx --include-inactive
```

---

## 9. Flujo de carrito y pedidos

### CartService (`apps/cart/services.py`)

- **Anonimo**: sesion (`request.session['cart']`)
- **Autenticado**: `CartItem` en BD
- **Login**: sesion se fusiona a BD automaticamente
- Clave de sesion: `"<product_id>:<variant_id>"` — mismo producto, distintos
  colores = filas separadas
- Los **servicios** (`item_type='service'`) no se agregan al carrito: lanzan
  `ValueError` orientando a solicitar cotización.

### OrderService (`apps/orders/services/order_service.py`)

```python
# Crear pedido (atomico, descuenta stock)
order = OrderService.create_from_cart(cart, user, address_data, payment_method)

# Confirmar pago desde webhook
OrderService.confirm_payment(order_id, gateway_amount=Decimal('350000'))

# Cambiar estado (restaura stock si cancela/reembolsa)
OrderService.change_status(order, 'cancelled')
```

### Politica de stock

| Evento | Efecto |
|--------|--------|
| Crear orden | Stock descontado |
| Confirmar pago | Sin cambio |
| Cancelar | Stock repuesto |
| Reembolsar | Stock repuesto |
| Operacion duplicada | Sin efecto (idempotente) |

`select_for_update` con bloqueo en orden estable (por ID) previene sobreventas
en concurrencia.

---

## 10. Pasarelas de pago

Las pasarelas **conectadas** (con vista de redirección + webhook en
`apps/payments/urls.py`, prefijo `/pagos/`):

| Pasarela | Servicio | Redirección | Webhook |
|----------|----------|-------------|---------|
| Wompi | `apps/payments/services/wompi.py` | `/pagos/wompi/<order_id>/` | `/pagos/wompi/webhook/` |
| PayU | `apps/payments/services/payu.py` | `/pagos/payu/<order_id>/` | `/pagos/payu/webhook/` (+ `/pagos/payu/respuesta/`) |
| MercadoPago | `apps/payments/services/mercadopago.py` | `/pagos/mp/<order_id>/` | `/pagos/mp/webhook/` |

Métodos sin pasarela online: **transferencia bancaria** y **contraentrega**
(`cash`) — crean la orden y muestran instrucciones / datos bancarios.

> **Stripe y PayPal:** existen módulos (`apps/payments/stripe.py`,
> `apps/payments/paypal.py`) con tests, pero **no están enrutados** todavía
> (no hay `path()` en `payments/urls.py`). Son base lista para crecer; no
> habilitarlos en el checkout hasta cablear sus vistas/webhooks.

**Seguridad implementada**: firma HMAC en Wompi, fail-closed si no hay clave
secreta configurada, idempotencia por `order.is_paid`, validacion de monto
contra `order.total_price`.

---

## 11. Comandos de gestión

```bash
# --- Catalogo ---
python manage.py sync_content
python manage.py import_catalog <ruta>
python manage.py sync_inventory_from_excel <archivo.xlsx>
python manage.py export_inventory_to_excel <salida.xlsx>
python manage.py export_inventory_to_excel salida.xlsx --include-inactive

# --- Pedidos ---
python manage.py cancel_expired_orders               # default 48h
python manage.py cancel_expired_orders --hours 24
python manage.py cancel_expired_orders --dry-run

# --- Django estandar ---
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
python manage.py check --deploy
```

---

## 12. Tests

```bash
# Suite completa (148 tests)
pytest

# Con cobertura
pytest --cov=apps --cov-report=term-missing

# Solo E2E
pytest tests/test_shop_e2e.py -v
```

Cobertura por dominio: `cart`, `catalog` (modelos, vistas, serializers,
import), `orders` (modelos, vistas, tasks), `payments` (vistas, stripe,
paypal), `users` (forms, modelos, vistas), `common`, y un E2E de la compra.

### Fixtures globales (`conftest.py`)

```python
def test_algo(product, authenticated_client):
    # product -> Product(stock=20)
    # authenticated_client -> Client con sesion activa
    ...
```

---

## 13. Despliegue a producción

### Render.com

1. Conectar repositorio en [render.com](https://render.com)
2. Render detecta `render.yaml` automaticamente (usa `requirements/prod.txt`)
3. Configurar en el panel **Environment** las variables secretas:
   - `SECRET_KEY`
   - `EMAIL_HOST_USER` + `EMAIL_HOST_PASSWORD`
   - Claves de pasarelas de pago
   - `SHOP_NAME`, `SHOP_CONTACT_PHONE`, `SHOP_CONTACT_EMAIL`, etc.

### Docker VPS

```bash
cp .env.example .env  # rellenar con valores de produccion
docker compose -f docker-compose.prod.yml up --build -d
docker compose -f docker-compose.prod.yml logs -f web
```

### Checklist de lanzamiento

```
[ ] SECRET_KEY en variable de entorno (nunca en codigo)
[ ] DEBUG=False (automatico en production.py)
[ ] DATABASE_URL -> PostgreSQL (no SQLite)
[ ] EMAIL_HOST_USER + EMAIL_HOST_PASSWORD configurados
[ ] SHOP_CONTACT_EMAIL -> buzón real (leads de cotización)
[ ] DJANGO_ALLOWED_HOSTS -> dominio real
[ ] CSRF_TRUSTED_ORIGINS -> https://tudominio.com
[ ] SECURE_SSL_REDIRECT=True
[ ] python manage.py check --deploy -> sin errores criticos
[ ] Webhooks de pasarelas apuntando al dominio de produccion
[ ] Cron job para cancel_expired_orders configurado
[ ] Backup automatico de PostgreSQL activado
[ ] CORS_ALLOWED_ORIGINS -> dominio real (si aplica)
```

### Cron job para pedidos expirados

```bash
# Ejecutar cada 6 horas (crontab o Render Cron Jobs)
0 */6 * * * cd /app && python manage.py cancel_expired_orders --hours 48
```

---

## 14. Mantenimiento día a día

### Añadir producto nuevo

```
1. Crear carpeta: content/categorias/<raiz>/<sub>/<producto>/
2. Crear data.json con: name, price, stock, description, brand, sku
3. Copiar imagenes a media/inventario/img/<cat>/<slug>/ (color en el nombre si aplica)
4. python manage.py sync_content
```

### Actualizar precios o stock

```bash
# Masivo (recomendado)
python manage.py export_inventory_to_excel catalogo.xlsx
# -> Editar en Excel
python manage.py sync_inventory_from_excel catalogo.xlsx

# Individual: Admin -> /admin/catalog/productvariant/
```

### Ciclo de vida de una orden

```
pending -> paid -> processing -> shipped -> delivered
   |                  |
   +-- cancelled      +-- refunded
```

Transiciones que restauran stock: `cancelled`, `refunded`.

### Backup PostgreSQL

```bash
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M).sql
psql  $DATABASE_URL < backup_YYYYMMDD_HHMM.sql
```

---

## 15. Convenciones y estilo

- **Formato**: Black (line-length 100) + isort (profile black)
- **Linting**: flake8 (max-line-length 100), excluye `migrations/`
- **Pre-commit**: `pre-commit install` activa los hooks automaticamente

```bash
make format && make lint && make test   # antes de cada commit
```

| Elemento | Convencion | Ejemplo |
|----------|-----------|---------|
| Slugs URL | kebab-case | `camara-ip-4mp` |
| SKUs | MAYUS-guiones | `CAM-IP-BLK-001` |
| Color en imagen | minusculas | `negro_01.jpg` |
| Variables Python | snake_case | `product_variant` |
| Clases Python | PascalCase | `ProductVariant` |
| Templates | snake_case.html | `product_detail.html` |

Migraciones: siempre con `makemigrations`; no editar las generadas salvo datos
iniciales; no hacer squash sin tests completos previos.

---

## 16. Cambios recientes (auditoría)

Auditoría completa de funcionamiento y coherencia comercial (2026-05-18):

| Cambio | Detalle |
|--------|---------|
| **API muerta/rota eliminada** | `/api/docs/` y `/api/redoc/` devolvían **HTTP 500** (`drf-yasg` no estaba en `INSTALLED_APPS`). No existía ninguna API real (sin `ViewSet`/router; serializers nunca importados). Se eliminó `drf_yasg` + `get_schema_view` + `api_urlpatterns` de `config/urls.py` y `drf-yasg` de `requirements/prod.txt`. Las rutas ahora dan 404 limpio. |
| **Bug de conversión en la landing** | El *feature box* "Monitoreos" enlazaba a `?categoria=monitoreos` (slug inexistente → página vacía). El slug real es `monitoreo`. Corregido en `templates/core/home.html`; ahora lista los servicios reales. |
| **Leads de contacto perdidos** | `ContactView` enviaba el formulario a `admin@tusitio.com` (placeholder hardcodeado). Ahora usa `settings.CONTACT_EMAIL` (← env `SHOP_CONTACT_EMAIL`) e incluye nombre/email del remitente en el cuerpo. `DEFAULT_FROM_EMAIL`/`SERVER_EMAIL` ahora vienen de variables de entorno. |
| **App `importer` eliminada** | App vacía (models/views/admin/apps/tests sin contenido); su único comando leía un directorio `imports/` inexistente y duplicaba `sync_content`. Eliminada del proyecto y de `INSTALLED_APPS`. |
| **`apps/core/permissions.py` eliminado** | Código muerto: nunca importado en ninguna parte. |
| **`requirements.txt` raíz reparado** | Estaba en UTF-16 y contenía dependencias de **otro proyecto** (metatrader5, scipy, rpy2, fastapi…). Reescrito en UTF-8 apuntando a `requirements/dev.txt`. El despliegue ya usaba `requirements/` (no se vio afectado). |
| **`estructura_proyecto.txt` eliminado** | Volcado de árbol de carpetas de 2.9 MB en UTF-16 — ruido sin valor. |

Validación: `manage.py check` limpio, sin migraciones pendientes, **148 tests
pasan**, todas las rutas comerciales verificadas por HTTP (200/302 correctos),
`/api/*` → 404 limpio, formulario de contacto entrega el email, el enlace de
monitoreo lista servicios reales.

---

## 17. Riesgos y limitaciones residuales

- **`SHOP_CONTACT_EMAIL` debe configurarse con un buzón real.** En el `.env`
  local el valor es un placeholder (`contacto@tudominio.com`). El mecanismo es
  correcto (env-driven), pero si no se pone un correo real en producción se
  perderán las cotizaciones. **Acción de lanzamiento obligatoria.**
- **Stripe y PayPal no están enrutados.** Hay módulos y tests, pero sin
  `path()` en `payments/urls.py`. No ofrecerlos en el checkout hasta cablear
  vistas y webhooks.
- **DRF sigue instalado pero sin endpoints.** `rest_framework` y
  `apps/catalog/serializers.py` (con tests) se conservan como base lista para
  una API futura (el brief pide estructura para crecer). Hoy no exponen nada;
  si no se va a construir API, pueden retirarse junto con sus tests.
- **Pasarelas en modo prueba.** Las claves por defecto en `development.py` son
  sandbox. Pagos reales requieren credenciales de producción en el entorno.
- **Catálogo de ejemplo.** La BD incluye datos de muestra (44 ítems, 75
  categorías). Reemplazar con catálogo real vía `content/` + `catalogo.xlsx`
  antes de lanzar.
- **`/cuentas/` y `/pagos/` no tienen índice** (404 en la raíz). Es por diseño
  (solo subrutas), no es un error.
- **Sin CI configurado.** Los tests existen y pasan en local; no hay pipeline
  automático que los corra en cada push.

---

## Stack tecnológico

| Tecnologia | Version | Uso |
|-----------|---------|-----|
| Python | 3.11 | Lenguaje base |
| Django | 5.2.3 | Framework web |
| django-allauth | 65.x | Autenticacion por email |
| PostgreSQL | 15 | BD en produccion |
| SQLite | — | Desarrollo local |
| Celery + Redis | 5.4 / 5.0 | Tareas asincronas |
| openpyxl | >=3.1 | Excel de inventario |
| Pillow | 10.4 | Procesamiento de imagenes |
| WhiteNoise | 6.7 | Estaticos en produccion |
| Gunicorn | 23.0 | Servidor WSGI |
| pytest-django | 4.11 | Suite de tests |

---

*Nexo YR Secure — Bogotá, Colombia*
