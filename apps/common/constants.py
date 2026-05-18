# beauty_shop\apps\common\constants.py
# =============================
# 🔁 Estados de Pedido
# =============================
ORDER_STATUS_PENDING = 'pending'
ORDER_STATUS_PAID = 'paid'
ORDER_STATUS_SHIPPED = 'shipped'
ORDER_STATUS_DELIVERED = 'delivered'
ORDER_STATUS_CANCELLED = 'cancelled'

ORDER_STATUS_CHOICES = [
    (ORDER_STATUS_PENDING, 'Pendiente'),
    (ORDER_STATUS_PAID, 'Pagado'),
    (ORDER_STATUS_SHIPPED, 'Enviado'),
    (ORDER_STATUS_DELIVERED, 'Entregado'),
    (ORDER_STATUS_CANCELLED, 'Cancelado'),
]

# =============================
# 💳 Métodos de pago
# =============================
PAYMENT_METHOD_STRIPE = 'stripe'
PAYMENT_METHOD_PAYPAL = 'paypal'
PAYMENT_METHOD_COD = 'cash_on_delivery'

PAYMENT_METHOD_CHOICES = [
    (PAYMENT_METHOD_STRIPE, 'Stripe'),
    (PAYMENT_METHOD_PAYPAL, 'PayPal'),
    (PAYMENT_METHOD_COD, 'Pago contra entrega'),
]

# =============================
# 🔐 Seguridad o configuración
# =============================
DEFAULT_CURRENCY = 'COP'
CART_SESSION_ID = 'cart'
MAX_UPLOAD_SIZE_MB = 5
