"""
Smoke test integral de extremo a extremo para la tienda Ares.

Un solo test (`test_shop_e2e`) ejecuta en orden los 7 bloques del checklist:

  1. Navegación principal (home, productos, servicios, navbar)
  2. Catálogo (categoría / subcategoría / producto)
  3. Carrito (add, badge, update, remove)
  4. Autenticación (login, navbar autenticado, logout)
  5. Checkout / orden (creación desde carrito, stock descontado)
  6. Pago (confirm_payment, rechazo de monto inválido, idempotencia)
  7. Inventario (stock final, cancelación repone, cancelación 2× no duplica)

No usa mocks de pasarelas: invoca `OrderService.confirm_payment` directamente
(la misma función que llaman los 3 webhooks), de modo que ejercita el código
real de validación de monto / idempotencia / atomicidad.

Idempotente: usa @pytest.mark.django_db con transacción aislada por test
(rollback al final), por lo que se puede correr N veces sin contaminar la BD.

Ejecutar:
    pytest tests/test_shop_e2e.py -v
    pytest tests/test_shop_e2e.py::test_shop_e2e -v -s     # con prints
"""
import re
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from apps.cart.models import CartItem
from apps.cart.services import CartService
from apps.catalog.models import Category, Product
from apps.orders.models import Order
from apps.orders.services.order_service import OrderService


# ────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────
def _step(label):
    """Imprime un encabezado visible al correr con `-s`. Útil al diagnosticar fallas."""
    print(f'\n──── {label} ────')


def _content_has(response, text):
    return text.encode() in response.content if isinstance(text, str) else text in response.content


# ────────────────────────────────────────────────────────────
# El test integral
# ────────────────────────────────────────────────────────────
@pytest.mark.django_db(transaction=True)
def test_shop_e2e():
    """Smoke test de extremo a extremo de toda la tienda."""

    # ════════════════════════════════════════════════════════
    # SETUP — usuario y producto controlado
    # ════════════════════════════════════════════════════════
    _step('SETUP')
    User = get_user_model()
    user, _ = User.objects.get_or_create(
        email='e2e@example.com',
        defaults={'username': 'e2etest'},
    )
    user.set_password('testpass-1234')
    user.save()

    # Crear catálogo mínimo determinístico: 1 raíz, 1 sub, 1 producto.
    # Uso modelos reales — la BD de test pytest-django parte vacía.
    root = Category.objects.create(
        name='E2E Categoría', slug='e2e-categoria',
        order=1, is_active=True,
    )
    sub = Category.objects.create(
        name='E2E Subcategoría', slug='e2e-subcategoria',
        parent=root, order=1, is_active=True,
    )
    initial_stock = 20
    product = Product.objects.create(
        name='E2E Cámara IP', slug='e2e-camara-ip',
        description='Producto para test de extremo a extremo.',
        price=Decimal('250000'),
        stock=initial_stock,
        category=sub,
        is_active=True,
        model_number='E2E-CAM-001',
    )
    print(f'  user={user.email}  product={product.slug}  stock={product.stock}  price={product.price}')

    client = Client()

    # ════════════════════════════════════════════════════════
    # 1. NAVEGACIÓN PRINCIPAL
    # ════════════════════════════════════════════════════════
    _step('1. Navegación principal')

    pages = {
        'home':       reverse('core:home'),
        'productos':  reverse('catalog:lista_productos'),
        'servicios':  reverse('catalog:product_list') + '?tipo=service',
        'login':      '/accounts/login/',
        'signup':     '/accounts/signup/',
    }
    for name, url in pages.items():
        r = client.get(url)
        assert r.status_code == 200, f'{name} ({url}) → {r.status_code}'
        print(f'  {name:12s} {url:30s} → 200')

    # Navbar y dropdowns presentes en el HTML del home
    home_html = client.get(pages['home']).content
    for marker in (b'class="ares-navbar', b'menu-categorias', b'submenu', b'nav-cart-link'):
        assert marker in home_html, f'Navbar marker faltante: {marker!r}'
    print('  navbar + dropdowns + cart icon: OK')

    # Anónimo: ve "Iniciar sesión" y "Registrarse", NO el menú de usuario logueado
    assert b'/accounts/login/' in home_html
    assert b'/accounts/signup/' in home_html
    assert b'/accounts/logout/' not in home_html, 'Anónimo no debería ver logout'

    # ════════════════════════════════════════════════════════
    # 2. CATÁLOGO
    # ════════════════════════════════════════════════════════
    _step('2. Catálogo')

    # Existe al menos 1 raíz, 1 sub, 1 producto.
    root_count = Category.objects.filter(parent__isnull=True, is_active=True).count()
    sub_count = Category.objects.filter(parent__isnull=False, is_active=True).count()
    prod_count = Product.objects.filter(is_active=True).count()
    assert root_count >= 1 and sub_count >= 1 and prod_count >= 1, \
        f'Catálogo vacío: roots={root_count} subs={sub_count} prods={prod_count}'
    print(f'  catálogo: {root_count} raíces / {sub_count} subs / {prod_count} productos')

    # Página de subcategoría (la del producto elegido)
    sub = product.category
    sub_url = reverse('catalog:product_by_category', kwargs={'category_slug': sub.slug})
    r = client.get(sub_url)
    assert r.status_code == 200, f'subcategoría {sub.slug} → {r.status_code}'
    assert product.name.encode() in r.content, 'producto NO aparece en su subcategoría'
    print(f'  subcategoría {sub.slug}: lista al producto')

    # Página raíz agrega productos de subs (fix anterior)
    if sub.parent:
        root_url = reverse('catalog:product_by_category', kwargs={'category_slug': sub.parent.slug})
        r = client.get(root_url)
        assert r.status_code == 200
        # Cualquier producto de cualquier sub debe aparecer en página de la raíz
        any_in_root = any(
            p.name.encode() in r.content for p in
            Product.objects.filter(category__parent=sub.parent, is_active=True)[:5]
        )
        assert any_in_root, 'raíz NO agrega productos de subs'
        print(f'  raíz {sub.parent.slug}: agrega productos de sus subs')

    # Detalle del producto
    detail_url = reverse('catalog:product_detail', kwargs={'slug': product.slug})
    r = client.get(detail_url)
    assert r.status_code == 200, f'detalle producto → {r.status_code}'
    assert product.name.encode() in r.content
    assert f'{int(product.price):,}'.replace(',', '.').encode() in r.content \
        or str(int(product.price)).encode() in r.content, 'precio NO renderiza'
    print(f'  detalle {product.slug}: nombre y precio renderizan')

    # ════════════════════════════════════════════════════════
    # 3. CARRITO (anónimo, sesión)
    # ════════════════════════════════════════════════════════
    _step('3. Carrito')

    # Add (POST con CSRF — Django test client lo maneja)
    r = client.post(
        reverse('cart:add_to_cart', kwargs={'product_id': product.id}),
        data={'quantity': 2},
        follow=True,
    )
    assert r.status_code == 200, f'add_to_cart → {r.status_code}'

    # Badge en navbar (cart_count en home)
    home_after_add = client.get(pages['home']).content
    m = re.search(rb'<span class="cart-badge">(\d+)</span>', home_after_add)
    assert m and int(m.group(1)) == 2, f'badge esperado=2 got={m.group(1) if m else None}'
    print('  add_to_cart=2 → badge=2')

    # Cart detail muestra el producto
    r = client.get(reverse('cart:cart_detail'))
    assert r.status_code == 200
    assert product.name.encode() in r.content, 'producto NO aparece en /carrito/'
    print('  cart_detail: muestra el ítem')

    # Update qty a 5
    r = client.post(
        reverse('cart:update', kwargs={'product_id': product.id}),
        data={'quantity': 5},
        follow=True,
    )
    home_after_upd = client.get(pages['home']).content
    m = re.search(rb'<span class="cart-badge">(\d+)</span>', home_after_upd)
    assert m and int(m.group(1)) == 5, 'badge no refleja update'
    print('  update qty → 5: badge=5')

    # Validación de stock: intentar update por encima de stock disponible
    r = client.post(
        reverse('cart:update', kwargs={'product_id': product.id}),
        data={'quantity': initial_stock + 100},
        follow=True,
    )
    home_after_bad = client.get(pages['home']).content
    m = re.search(rb'<span class="cart-badge">(\d+)</span>', home_after_bad)
    assert m and int(m.group(1)) == 5, 'cart NO debe aceptar más unidades que el stock'
    print(f'  update qty>stock ({initial_stock + 100}): bloqueado, badge sigue=5')

    # Remove
    client.post(reverse('cart:remove', kwargs={'product_id': product.id}))
    home_after_rm = client.get(pages['home']).content
    assert b'<span class="cart-badge">' not in home_after_rm, 'badge debería desaparecer'
    print('  remove: badge ausente (cart vacío)')

    # ════════════════════════════════════════════════════════
    # 4. AUTENTICACIÓN
    # ════════════════════════════════════════════════════════
    _step('4. Autenticación')

    # Login con force_login (el flujo de credenciales con allauth tiene su propio test)
    client.force_login(user)
    home_logged = client.get(pages['home']).content

    # Navbar autenticado: logout form + profile + orders
    assert b'/accounts/logout/' in home_logged, 'falta form de logout'
    assert reverse('users:profile').encode() in home_logged, 'falta link a profile'
    assert reverse('orders:order_list').encode() in home_logged, 'falta link a pedidos'
    # Y ya no muestra "Iniciar sesión" / "Registrarse"
    assert b'/accounts/login/' not in home_logged, 'no debería mostrar login'
    print('  navbar autenticado: profile + orders + logout form OK')

    # Profile y order_list responden 200 (antes redirigían a login)
    r = client.get(reverse('users:profile'))
    assert r.status_code == 200, f'profile → {r.status_code}'
    r = client.get(reverse('orders:order_list'))
    assert r.status_code == 200, f'order_list → {r.status_code}'
    print('  /cuentas/profile/ y /pedidos/ responden 200')

    # ════════════════════════════════════════════════════════
    # 5. CHECKOUT / ORDEN — vía OrderService (mismo código que la view)
    # ════════════════════════════════════════════════════════
    _step('5. Checkout / orden')

    # Limpiar y armar carrito como autenticado (BD)
    CartItem.objects.filter(user=user).delete()
    client.post(
        reverse('cart:add_to_cart', kwargs={'product_id': product.id}),
        data={'quantity': 3},
    )
    cart_qty_before_order = CartItem.objects.get(user=user, product=product).quantity
    assert cart_qty_before_order == 3
    print(f'  cart preparado: qty={cart_qty_before_order}')

    # Construir CartService desde un request real (la view hace lo mismo)
    from django.test import RequestFactory
    from django.contrib.sessions.backends.db import SessionStore
    rf = RequestFactory()
    req = rf.get('/'); req.user = user; req.session = SessionStore(); req.session.create()
    cart = CartService(req)

    address = {
        'name': 'Cliente E2E', 'phone': '+57 300 1234567',
        'address': 'Cra 7 # 100-01', 'city': 'Bogotá',
        'department': 'Cundinamarca', 'postal_code': '110111',
    }
    product.refresh_from_db()
    stock_before_order = product.stock

    order = OrderService.create_from_cart(
        cart_service=cart, user=user, address_data=address, payment_method='wompi',
    )
    assert order.status == 'pending', f'estado inicial esperado=pending got={order.status}'
    assert order.reference, 'referencia debe estar generada'
    assert order.total_price > 0, 'total > 0'
    product.refresh_from_db()
    assert product.stock == stock_before_order - 3, \
        f'stock no descontó: antes={stock_before_order} después={product.stock}'
    print(f'  orden ref={order.reference} total={order.total_price} | stock {stock_before_order}→{product.stock}')

    # ════════════════════════════════════════════════════════
    # 6. PAGO — confirm_payment (mismo path que webhooks reales)
    # ════════════════════════════════════════════════════════
    _step('6. Pago')

    # 6a. Monto inválido → RECHAZADO
    rejected = OrderService.confirm_payment(
        order_reference=order.reference,
        payment_id='TX-FAKE-LOW',
        gateway_name='wompi',
        gateway_amount=Decimal('1.00'),  # monto absurdo
    )
    assert rejected is None, 'pago con monto inválido NO debe confirmar'
    order.refresh_from_db()
    assert order.status == 'pending', 'orden debe seguir pending tras rechazo'
    print('  pago con monto inválido: RECHAZADO, orden sigue pending')

    # 6b. Monto correcto → APROBADO
    paid = OrderService.confirm_payment(
        order_reference=order.reference,
        payment_id='TX-WOMPI-OK',
        gateway_name='wompi',
        gateway_amount=order.total_price,
    )
    assert paid is not None and paid.is_paid, 'pago válido debe marcar paid'
    assert paid.payment_id == 'TX-WOMPI-OK'
    print(f'  pago correcto: orden→paid, payment_id={paid.payment_id}')

    # 6c. Webhook duplicado (idempotencia)
    paid_again = OrderService.confirm_payment(
        order_reference=order.reference,
        payment_id='TX-WOMPI-OK',
        gateway_name='wompi',
        gateway_amount=order.total_price,
    )
    assert paid_again.status == 'paid'
    # Stock NO debe descontar de nuevo (ya estaba descontado al crear)
    product.refresh_from_db()
    assert product.stock == stock_before_order - 3, 'idempotencia: stock no debe cambiar'
    # Solo un log de transición → 'paid' (no dos)
    paid_logs = paid_again.logs.filter(new_status='paid').count()
    assert paid_logs == 1, f'duplicación de log: encontrados {paid_logs} logs paid'
    print(f'  webhook repetido: idempotente (stock={product.stock}, logs paid={paid_logs})')

    # ════════════════════════════════════════════════════════
    # 7. INVENTARIO — cancelación repone, no duplica
    # ════════════════════════════════════════════════════════
    _step('7. Inventario')

    # Crear una segunda orden para probar cancelación
    CartItem.objects.update_or_create(
        user=user, product=product, defaults={'quantity': 2},
    )
    cart2 = CartService(req)
    order2 = OrderService.create_from_cart(cart2, user, address, payment_method='cash')
    product.refresh_from_db()
    stock_after_order2 = product.stock
    print(f'  orden2 ref={order2.reference} | stock tras 2ª orden={stock_after_order2}')

    # Cancelar — repone stock
    OrderService.change_status(order2, 'cancelled', source='test', note='cancelación e2e')
    product.refresh_from_db()
    assert product.stock == stock_after_order2 + 2, \
        f'cancelar no repuso: esperado={stock_after_order2 + 2} got={product.stock}'
    print(f'  cancelar orden2: stock {stock_after_order2}→{product.stock} (+2)')

    # Cancelar de nuevo — NO duplica
    OrderService.change_status(order2, 'cancelled', source='test', note='retry')
    product.refresh_from_db()
    assert product.stock == stock_after_order2 + 2, 'cancelar 2× NO debe duplicar reposición'
    print('  cancelar 2× orden2: stock estable (no duplica)')

    # No-sobreventa: pedir más unidades de las disponibles
    Product.objects.filter(pk=product.pk).update(stock=1)
    CartItem.objects.update_or_create(
        user=user, product=product, defaults={'quantity': 5},
    )
    cart3 = CartService(req)
    with pytest.raises(ValueError, match=r'(?i)stock'):
        OrderService.create_from_cart(cart3, user, address, payment_method='wompi')
    product.refresh_from_db()
    assert product.stock == 1, 'sobreventa intentada: stock NO debe cambiar'
    print('  intento sobreventa: ValueError correcto, stock intacto')

    # ════════════════════════════════════════════════════════
    # CIERRE — logout
    # ════════════════════════════════════════════════════════
    _step('CIERRE — logout')
    csrf_token = client.cookies.get('csrftoken')
    r = client.post('/accounts/logout/',
                    data={'csrfmiddlewaretoken': csrf_token.value if csrf_token else ''},
                    follow=True)
    assert r.status_code in (200, 302), f'logout → {r.status_code}'
    home_anon = client.get(pages['home']).content
    assert b'/accounts/login/' in home_anon, 'tras logout, navbar debe mostrar login'
    print('  logout exitoso, navbar vuelve a anónimo')

    print('\n══════ E2E PASS ══════')
