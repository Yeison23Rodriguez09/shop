# apps/orders/forms.py
from django import forms

DEPARTAMENTOS_COLOMBIA = [
    ('', 'Seleccione departamento…'),
    ('Amazonas', 'Amazonas'), ('Antioquia', 'Antioquia'), ('Arauca', 'Arauca'),
    ('Atlántico', 'Atlántico'), ('Bolívar', 'Bolívar'), ('Boyacá', 'Boyacá'),
    ('Caldas', 'Caldas'), ('Caquetá', 'Caquetá'), ('Casanare', 'Casanare'),
    ('Cauca', 'Cauca'), ('Cesar', 'Cesar'), ('Chocó', 'Chocó'),
    ('Córdoba', 'Córdoba'), ('Cundinamarca', 'Cundinamarca'), ('Guainía', 'Guainía'),
    ('Guaviare', 'Guaviare'), ('Huila', 'Huila'), ('La Guajira', 'La Guajira'),
    ('Magdalena', 'Magdalena'), ('Meta', 'Meta'), ('Nariño', 'Nariño'),
    ('Norte de Santander', 'Norte de Santander'), ('Putumayo', 'Putumayo'),
    ('Quindío', 'Quindío'), ('Risaralda', 'Risaralda'),
    ('San Andrés y Providencia', 'San Andrés y Providencia'),
    ('Santander', 'Santander'), ('Sucre', 'Sucre'), ('Tolima', 'Tolima'),
    ('Valle del Cauca', 'Valle del Cauca'), ('Vaupés', 'Vaupés'), ('Vichada', 'Vichada'),
    ('Bogotá D.C.', 'Bogotá D.C.'),
]

PAYMENT_METHOD_CHOICES = [
    ('transfer', 'Transferencia bancaria'),
    ('cash', 'Pago contraentrega (efectivo)'),
    ('wompi', 'Wompi — Tarjeta / PSE / Nequi / Bancolombia'),
    ('payu', 'PayU — Tarjeta crédito / débito / PSE'),
    ('mercadopago', 'MercadoPago — Tarjeta / PSE / efectivo'),
]


def get_available_payment_methods():
    """
    Devuelve solo los métodos de pago habilitados según .env.
    Los métodos manuales (transferencia / contraentrega) siempre están disponibles.
    Las pasarelas externas se muestran únicamente si tienen credenciales configuradas.
    """
    from django.conf import settings as dj_settings
    methods = [
        ('transfer', 'Transferencia bancaria'),
        ('cash', 'Pago contraentrega (efectivo)'),
    ]
    if getattr(dj_settings, 'WOMPI_PUBLIC_KEY', '') and not str(getattr(dj_settings, 'WOMPI_PUBLIC_KEY', '')).startswith('pub_test_xxx'):
        methods.append(('wompi', 'Wompi — Tarjeta / PSE / Nequi / Bancolombia'))
    if getattr(dj_settings, 'PAYU_API_KEY', '') and getattr(dj_settings, 'PAYU_API_KEY', '') != '4Vj8eK4rloUd272L48hsrarnUA':
        methods.append(('payu', 'PayU — Tarjeta crédito / débito / PSE'))
    if getattr(dj_settings, 'MP_ACCESS_TOKEN', '') and not str(getattr(dj_settings, 'MP_ACCESS_TOKEN', '')).startswith('TEST-xxx'):
        methods.append(('mercadopago', 'MercadoPago — Tarjeta / PSE / efectivo'))
    return methods


class CheckoutAddressForm(forms.Form):
    """Paso 1: dirección de entrega."""
    name = forms.CharField(
        label='Nombre completo del destinatario',
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre y apellido'}),
    )
    phone = forms.CharField(
        label='Teléfono / WhatsApp',
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+57 300 000 0000'}),
    )
    address = forms.CharField(
        label='Dirección de entrega',
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Calle 45 # 12-30, Apto 301, Barrio Centro'
        }),
    )
    city = forms.CharField(
        label='Ciudad',
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bogotá'}),
    )
    department = forms.ChoiceField(
        label='Departamento',
        choices=DEPARTAMENTOS_COLOMBIA,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    postal_code = forms.CharField(
        label='Código postal',
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '110111 (opcional)'}),
    )
    notes = forms.CharField(
        label='Instrucciones de entrega',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Indicaciones para el transportista (opcional)'
        }),
    )
    save_address = forms.BooleanField(
        label='Guardar esta dirección en mi perfil',
        required=False,
        initial=True,
    )


class CheckoutPaymentForm(forms.Form):
    """Paso 2: método de pago. Solo muestra los métodos que están realmente
    habilitados (manuales siempre, pasarelas solo si hay credenciales)."""
    payment_method = forms.ChoiceField(
        label='Método de pago',
        choices=PAYMENT_METHOD_CHOICES,  # se reemplaza dinámicamente en __init__
        widget=forms.RadioSelect(attrs={'class': 'payment-radio'}),
        initial='transfer',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = get_available_payment_methods()
        self.fields['payment_method'].choices = choices
        # Forzar default al primer método disponible
        if choices and not self.initial.get('payment_method'):
            self.fields['payment_method'].initial = choices[0][0]
