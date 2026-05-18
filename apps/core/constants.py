# beauty_shop\apps\core\constants.py
# --- Estados de pedido ---
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


# --- Roles de usuario personalizados ---
ROLE_ADMIN = 'admin'
ROLE_CUSTOMER = 'customer'
ROLE_SELLER = 'seller'

USER_ROLES = [
    (ROLE_ADMIN, 'Administrador'),
    (ROLE_CUSTOMER, 'Cliente'),
    (ROLE_SELLER, 'Vendedor'),
]


# --- Categorías fijas (ejemplo para blog o productos) ---
DEFAULT_CATEGORIES = [
    'Belleza',
    'Maquillaje',
    'Cuidado personal',
    'Cabello',
    'Uñas',
]


# --- Otras constantes útiles ---
CURRENCY_SYMBOL = '$'
SITE_NAME = 'Nexo YR Secure'
SUPPORT_EMAIL = 'soporte@aresseguridad.com'
