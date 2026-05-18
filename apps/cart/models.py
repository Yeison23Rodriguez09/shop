# apps/cart/models.py
from django.db import models
from django.conf import settings
from apps.catalog.models import Product, ProductVariant


class CartItem(models.Model):
    """
    Ítem del carrito persistente en base de datos.
    Solo para usuarios autenticados. Los anónimos usan sesión.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name='Usuario',
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name='Producto',
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name='cart_items',
        null=True, blank=True,
        verbose_name='Variante',
    )
    quantity = models.PositiveIntegerField('Cantidad', default=1)
    added_at = models.DateTimeField('Agregado el', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado el', auto_now=True)

    class Meta:
        unique_together = ('user', 'product', 'variant')
        verbose_name = 'Ítem de carrito'
        verbose_name_plural = 'Ítems de carrito'
        ordering = ['added_at']

    def __str__(self):
        v = f' [{self.variant.color}]' if self.variant_id else ''
        return f'{self.user.email} — {self.product.name}{v} x{self.quantity}'

    @property
    def unit_price(self):
        return self.variant.price if self.variant_id else self.product.price

    @property
    def subtotal(self):
        return self.unit_price * self.quantity
