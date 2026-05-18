"""Smoke test de los flujos de inventario y pagos."""
import os, sys, django
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.development'
django.setup()

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import Client
from apps.cart.services import CartService
from apps.catalog.models import Product
from apps.orders.models import Order
from apps.orders.services.order_service import OrderService

U = get_user_model()
fails = 0


def assert_eq(label, got, want):
    global fails
    ok = got == want
    if not ok:
        fails += 1
    print(f'  {"✓" if ok else "✗"} {label}: got={got!r} want={want!r}')


def assert_true(label, cond):
    global fails
    if not cond:
        fails += 1
    print(f'  {"✓" if cond else "✗"} {label}')


print('=== Setup ===')
user, _ = U.objects.get_or_create(email='inv-test@example.com', defaults={'username': 'invtest'})
user.set_password('x'); user.save()

# Producto controlado para los tests
prod = Product.objects.first()
prod.stock = 10
prod.save(update_fields=['stock'])
print(f'  product={prod.name} | initial stock={prod.stock} | price={prod.price}')

print()
print('=== 1) CartService valida stock al agregar ===')
c = Client(); c.force_login(user)
# Limpiar carrito por si quedó algo
from apps.cart.models import CartItem
CartItem.objects.filter(user=user).delete()

cs = type('FakeReq', (), {'user': user, 'session': c.session, 'POST': {}})
# Usamos test client real para garantizar sesión
r = c.post(f'/carrito/add/{prod.id}/', {'quantity': 5}, follow=True)
assert_eq('add 5 unidades válido', r.status_code, 200)
items = CartItem.objects.filter(user=user, product=prod).first()
assert_eq('en BD: cantidad', items.quantity if items else 0, 5)

# Intentar agregar 8 más → 5+8=13 > 10 → debe fallar
r = c.post(f'/carrito/add/{prod.id}/', {'quantity': 8}, follow=True)
items = CartItem.objects.filter(user=user, product=prod).first()
assert_eq('add que excede stock NO se aplica', items.quantity, 5)
assert_true('mensaje de error visible', b'Stock insuficiente' in r.content or b'insuficiente' in r.content)

# Update a 10 (válido) y luego a 99 (inválido)
c.post(f'/carrito/update/{prod.id}/', {'quantity': 10})
items.refresh_from_db()
assert_eq('update a max stock', items.quantity, 10)
c.post(f'/carrito/update/{prod.id}/', {'quantity': 99})
items.refresh_from_db()
assert_eq('update sobre stock NO se aplica', items.quantity, 10)

print()
print('=== 2) Crear orden desde carrito (atómico, select_for_update) ===')
prod.refresh_from_db()
stock_before = prod.stock
cart = CartService.__new__(CartService)
# Construir CartService con un request simulado
from django.test import RequestFactory
rf = RequestFactory()
req = rf.get('/'); req.user = user
from django.contrib.sessions.backends.db import SessionStore
req.session = SessionStore(); req.session.create()
cart.__init__(req)
# Force-add via internal API (saltando view) — el cart ya tiene 10 en BD
# pero el request es nuevo (session), por lo que CartService usa BD si user auth.
items = cart.get_items()
assert_eq('cart_items en BD', len(items), 1)
assert_eq('cart qty', items[0]['quantity'], 10)

addr = {'name': 'Test', 'phone': '+57 300 0000000', 'address': 'Cra 1', 'city': 'Bogota'}
order = OrderService.create_from_cart(cart, user, addr, payment_method='wompi')
assert_true('orden creada con referencia', bool(order.reference))
assert_eq('orden status', order.status, 'pending')
prod.refresh_from_db()
assert_eq('stock descontado', prod.stock, stock_before - 10)

print()
print('=== 3) Validar stock insuficiente en checkout (concurrencia) ===')
# Agregar más al carrito de otro usuario para que el primero ya quedó sin stock
prod.refresh_from_db()
print(f'  stock actual: {prod.stock}')
user2, _ = U.objects.get_or_create(email='inv-test-2@example.com', defaults={'username': 'invtest2'})
user2.set_password('x'); user2.save()
CartItem.objects.filter(user=user2).delete()
c2 = Client(); c2.force_login(user2)
# user2 intenta agregar 1 (puede o no haber stock)
if prod.stock > 0:
    c2.post(f'/carrito/add/{prod.id}/', {'quantity': prod.stock})
    cart2 = CartService.__new__(CartService)
    req2 = rf.get('/'); req2.user = user2
    req2.session = SessionStore(); req2.session.create()
    cart2.__init__(req2)
    # Mientras tanto, alguien (admin) baja el stock por debajo
    Product.objects.filter(pk=prod.pk).update(stock=0)
    # create_from_cart debe abortar por validación atómica
    try:
        OrderService.create_from_cart(cart2, user2, addr, payment_method='wompi')
        assert_true('debe lanzar ValueError por stock insuficiente', False)
    except ValueError as e:
        assert_true(f'ValueError esperado: {str(e)[:50]}...', True)

print()
print('=== 4) Idempotencia + monto en confirm_payment ===')
prod.stock = 50; prod.save(update_fields=['stock'])
# Crear nueva orden con un solo item
CartItem.objects.filter(user=user).delete()
CartItem.objects.update_or_create(user=user, product=prod, defaults={'quantity': 1})
cart3 = CartService.__new__(CartService)
req3 = rf.get('/'); req3.user = user; req3.session = SessionStore(); req3.session.create()
cart3.__init__(req3)
order = OrderService.create_from_cart(cart3, user, addr, payment_method='wompi')
print(f'  orden creada ref={order.reference} total={order.total_price}')

# Confirmar con monto correcto
o = OrderService.confirm_payment(order.reference, 'TX-GOOD-1', 'wompi',
                                 gateway_amount=order.total_price)
assert_true('confirmacion exitosa', o is not None and o.is_paid)
assert_eq('orden status=paid', o.status, 'paid')

# Re-llamar — idempotente
o2 = OrderService.confirm_payment(order.reference, 'TX-GOOD-1', 'wompi',
                                  gateway_amount=order.total_price)
assert_eq('idempotencia: status sigue paid', o2.status, 'paid')
# Verificar que no se descontó stock dos veces (ya estaba descontado al crear)
expected_stock = 50 - 1
prod.refresh_from_db()
assert_eq('stock NO duplicado por idempotencia', prod.stock, expected_stock)

# Confirmar con monto MAL — debe rechazar
CartItem.objects.update_or_create(user=user, product=prod, defaults={'quantity': 1})
cart4 = CartService.__new__(CartService)
req4 = rf.get('/'); req4.user = user; req4.session = SessionStore(); req4.session.create()
cart4.__init__(req4)
order_bad = OrderService.create_from_cart(cart4, user, addr, payment_method='wompi')
result = OrderService.confirm_payment(order_bad.reference, 'TX-BAD', 'wompi',
                                      gateway_amount=Decimal('1.00'))
assert_true('webhook con monto mismatch RECHAZADO (None)', result is None)
order_bad.refresh_from_db()
assert_eq('orden NO fue marcada paid', order_bad.status, 'pending')

print()
print('=== 5) Cancelación repone stock ===')
prod.refresh_from_db()
stock_before_cancel = prod.stock
qty = order_bad.items.first().quantity
OrderService.change_status(order_bad, 'cancelled', note='test cancel', source='test')
prod.refresh_from_db()
assert_eq('stock repuesto al cancelar', prod.stock, stock_before_cancel + qty)
# Idempotencia: cancelar otra vez no duplica
OrderService.change_status(order_bad, 'cancelled', note='retry', source='test')
prod.refresh_from_db()
assert_eq('cancelar 2 veces NO duplica reposicion', prod.stock, stock_before_cancel + qty)

print()
print('=== 6) Reembolso también repone (orden paid) ===')
order.refresh_from_db()
prod.refresh_from_db()
stock_before_refund = prod.stock
qty = order.items.first().quantity
OrderService.change_status(order, 'refunded', note='test refund', source='test')
prod.refresh_from_db()
assert_eq('stock repuesto al reembolsar', prod.stock, stock_before_refund + qty)

print()
print(f'=== RESULTADO: {"PASS" if fails == 0 else f"FAIL ({fails} aserciones)"} ===')
sys.exit(0 if fails == 0 else 1)
