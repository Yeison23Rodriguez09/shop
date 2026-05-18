# apps/cart/services.py
"""
CartService — Carrito hibrido con soporte de variantes.

  - Usuario autenticado  → CartItem en BD (persiste entre sesiones).
  - Usuario anonimo      → Sesion Django (clave: f'{product_id}:{variant_id or ""}').
  - merge_session_into_db al hacer login.

Variantes:
  - Si product no tiene variantes activas, add(product) usa product.price/stock.
  - Si product tiene variantes, add(product, variant=v) usa variant.price/stock.
  - El mismo producto con dos colores son DOS lineas distintas en el carrito
    (clave compuesta product+variant).
"""
from decimal import Decimal
from django.conf import settings
from apps.catalog.models import Product, ProductVariant


class CartService:

    def __init__(self, request):
        self.request = request
        self.user = request.user if request.user.is_authenticated else None
        self.session = request.session

        if settings.CART_SESSION_ID not in self.session:
            self.session[settings.CART_SESSION_ID] = {}
        self._session_cart = self.session[settings.CART_SESSION_ID]

    # ── Helpers de clave/precio/stock ───────────────────────
    @staticmethod
    def _session_key(product, variant):
        return f'{product.id}:{variant.id if variant else ""}'

    @staticmethod
    def _effective_price(product, variant):
        return variant.price if variant else product.price

    @staticmethod
    def _effective_stock(product, variant):
        return variant.stock if variant else product.stock

    # ── Escritura ────────────────────────────────────────────
    def add(self, product, quantity=1, override_quantity=False, variant=None):
        """
        Agrega o actualiza una linea del carrito. Si product tiene variantes,
        `variant` es obligatorio (de lo contrario se interpreta como producto
        sin variantes; util para legacy y backward compat).

        Lanza ValueError ante:
          - producto/variante inactiva
          - cantidad <= 0
          - cantidad final > stock disponible
        """
        if getattr(product, 'item_type', 'product') == 'service':
            raise ValueError(
                f'"{product.name}" es un servicio: solicita una cotización, '
                f'no se agrega al carrito.'
            )
        if not product.is_active:
            raise ValueError(f'El producto "{product.name}" no esta disponible.')
        if variant is not None:
            if variant.product_id != product.id:
                raise ValueError('La variante no pertenece a este producto.')
            if not variant.is_active:
                raise ValueError(f'La variante {variant.color} no esta disponible.')
        if quantity <= 0:
            raise ValueError('La cantidad debe ser mayor a cero.')

        existing = 0 if override_quantity else self._current_quantity(product, variant)
        target = quantity if override_quantity else existing + quantity
        stock = self._effective_stock(product, variant)
        if target > stock:
            label = f'{product.name}' + (f' ({variant.color})' if variant else '')
            raise ValueError(
                f'Stock insuficiente para "{label}". '
                f'Disponible: {stock}, en carrito: {existing}, solicitado: {quantity}.'
            )

        if self.user:
            self._db_add(product, variant, quantity, override_quantity)
        else:
            self._session_add(product, variant, quantity, override_quantity)

    def _current_quantity(self, product, variant=None):
        if self.user:
            from apps.cart.models import CartItem
            row = CartItem.objects.filter(
                user=self.user, product=product, variant=variant,
            ).only('quantity').first()
            return row.quantity if row else 0
        return self._session_cart.get(self._session_key(product, variant),
                                      {}).get('quantity', 0)

    def remove(self, product, variant=None):
        if self.user:
            self._db_remove(product, variant)
        else:
            self._session_remove(product, variant)

    def clear(self):
        if self.user:
            from apps.cart.models import CartItem
            CartItem.objects.filter(user=self.user).delete()
        self._session_cart.clear()
        self.session.modified = True

    def update_quantity(self, product, quantity, variant=None):
        if quantity <= 0:
            self.remove(product, variant)
            return
        self.add(product, quantity, override_quantity=True, variant=variant)

    # ── Lectura ──────────────────────────────────────────────
    def get_items(self):
        if self.user:
            return self._db_get_items()
        return self._session_get_items()

    def get_total_price(self):
        return sum(item['total_price'] for item in self.get_items())

    def get_item_count(self):
        return sum(item['quantity'] for item in self.get_items())

    def __len__(self):
        return self.get_item_count()

    # ── Fusion al hacer login ────────────────────────────────
    def merge_session_into_db(self):
        if not self.user:
            return
        session_data = self._session_cart.copy()
        if not session_data:
            return

        # Resolver productos y variantes en lotes.
        product_ids = set()
        variant_ids = set()
        for key in session_data:
            pid, _, vid = key.partition(':')
            product_ids.add(int(pid))
            if vid:
                variant_ids.add(int(vid))

        products = {p.id: p for p in Product.objects.filter(id__in=product_ids)}
        variants = {v.id: v for v in ProductVariant.objects.filter(id__in=variant_ids)} if variant_ids else {}

        for key, item in session_data.items():
            pid, _, vid = key.partition(':')
            product = products.get(int(pid))
            variant = variants.get(int(vid)) if vid else None
            if product:
                self._db_add(product, variant, item['quantity'], override_quantity=False)

        self._session_cart.clear()
        self.session.modified = True

    # ── BD privados ──────────────────────────────────────────
    def _db_add(self, product, variant, quantity, override_quantity):
        from apps.cart.models import CartItem
        item, _ = CartItem.objects.get_or_create(
            user=self.user, product=product, variant=variant,
            defaults={'quantity': 0},
        )
        if override_quantity:
            item.quantity = quantity
        else:
            item.quantity += quantity
        item.save()

    def _db_remove(self, product, variant=None):
        from apps.cart.models import CartItem
        CartItem.objects.filter(user=self.user, product=product, variant=variant).delete()

    def _db_get_items(self):
        from apps.cart.models import CartItem
        items = CartItem.objects.filter(user=self.user).select_related(
            'product', 'product__brand', 'product__category', 'variant',
        )
        result = []
        for item in items:
            price = item.unit_price
            result.append({
                'product': item.product,
                'variant': item.variant,
                'quantity': item.quantity,
                'price': price,
                'total_price': price * item.quantity,
            })
        return result

    # ── Sesion privados ──────────────────────────────────────
    def _session_add(self, product, variant, quantity, override_quantity):
        key = self._session_key(product, variant)
        if key not in self._session_cart:
            self._session_cart[key] = {
                'quantity': 0,
                'price': str(self._effective_price(product, variant)),
                'product_id': product.id,
                'variant_id': variant.id if variant else None,
            }
        if override_quantity:
            self._session_cart[key]['quantity'] = quantity
        else:
            self._session_cart[key]['quantity'] += quantity
        self.session.modified = True

    def _session_remove(self, product, variant=None):
        key = self._session_key(product, variant)
        if key in self._session_cart:
            del self._session_cart[key]
            self.session.modified = True

    def _session_get_items(self):
        if not self._session_cart:
            return []

        # Recolectar ids
        product_ids, variant_ids = set(), set()
        for key in self._session_cart:
            pid, _, vid = key.partition(':')
            product_ids.add(int(pid))
            if vid:
                variant_ids.add(int(vid))

        products = {p.id: p for p in Product.objects.filter(id__in=product_ids)}
        variants = {v.id: v for v in ProductVariant.objects.filter(id__in=variant_ids)} if variant_ids else {}

        result = []
        for key, item in self._session_cart.items():
            pid, _, vid = key.partition(':')
            product = products.get(int(pid))
            variant = variants.get(int(vid)) if vid else None
            if product:
                price = Decimal(item['price'])
                qty = item['quantity']
                result.append({
                    'product': product,
                    'variant': variant,
                    'quantity': qty,
                    'price': price,
                    'total_price': price * qty,
                })
        return result
