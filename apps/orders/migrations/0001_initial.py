import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('catalog', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(blank=True, help_text='Generada automáticamente.', max_length=32, unique=True, verbose_name='Referencia única')),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'Pendiente de pago'),
                        ('paid', 'Pagado'),
                        ('processing', 'En preparación'),
                        ('shipped', 'Enviado'),
                        ('delivered', 'Entregado'),
                        ('cancelled', 'Cancelado'),
                        ('refunded', 'Reembolsado'),
                    ],
                    default='pending',
                    max_length=20,
                    verbose_name='Estado',
                )),
                ('payment_method', models.CharField(
                    blank=True,
                    choices=[
                        ('wompi', 'Wompi (Bancolombia)'),
                        ('payu', 'PayU'),
                        ('mercadopago', 'MercadoPago'),
                        ('transfer', 'Transferencia bancaria'),
                        ('cash', 'Pago en efectivo (contraentrega)'),
                    ],
                    max_length=20,
                    verbose_name='Método de pago',
                )),
                ('payment_id', models.CharField(blank=True, max_length=200, verbose_name='ID de transacción (pasarela)')),
                ('paid_at', models.DateTimeField(blank=True, null=True, verbose_name='Fecha de pago')),
                ('subtotal', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Subtotal')),
                ('shipping_cost', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Costo de envío')),
                ('total_price', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Total')),
                ('shipping_name', models.CharField(blank=True, max_length=200, verbose_name='Nombre destinatario')),
                ('shipping_phone', models.CharField(blank=True, max_length=30, verbose_name='Teléfono')),
                ('shipping_address', models.CharField(blank=True, max_length=255, verbose_name='Dirección')),
                ('shipping_city', models.CharField(blank=True, max_length=100, verbose_name='Ciudad')),
                ('shipping_department', models.CharField(blank=True, max_length=100, verbose_name='Departamento')),
                ('shipping_postal_code', models.CharField(blank=True, max_length=10, verbose_name='Código postal')),
                ('shipping_notes', models.TextField(blank=True, verbose_name='Instrucciones de entrega')),
                ('internal_notes', models.TextField(blank=True, verbose_name='Notas internas')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creado el')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Actualizado el')),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='orders',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Cliente',
                )),
            ],
            options={
                'verbose_name': 'Orden',
                'verbose_name_plural': 'Órdenes',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_name', models.CharField(max_length=200, verbose_name='Nombre del producto')),
                ('product_model', models.CharField(blank=True, max_length=100, verbose_name='Modelo')),
                ('quantity', models.PositiveIntegerField(default=1, verbose_name='Cantidad')),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Precio unitario')),
                ('order', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='items',
                    to='orders.order',
                    verbose_name='Orden',
                )),
                ('product', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to='catalog.product',
                    verbose_name='Producto',
                )),
            ],
            options={
                'verbose_name': 'Ítem de orden',
                'verbose_name_plural': 'Ítems de orden',
            },
        ),
        migrations.CreateModel(
            name='OrderLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('previous_status', models.CharField(blank=True, max_length=20, verbose_name='Estado anterior')),
                ('new_status', models.CharField(max_length=20, verbose_name='Nuevo estado')),
                ('note', models.TextField(blank=True, help_text='Razón del cambio, mensaje al cliente, etc.', verbose_name='Nota')),
                ('source', models.CharField(
                    default='system',
                    help_text='system / admin / webhook_wompi / webhook_payu / webhook_mp',
                    max_length=30,
                    verbose_name='Origen',
                )),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Registrado el')),
                ('changed_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='order_logs',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Cambiado por',
                )),
                ('order', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='logs',
                    to='orders.order',
                    verbose_name='Orden',
                )),
            ],
            options={
                'verbose_name': 'Log de orden',
                'verbose_name_plural': 'Logs de órdenes',
                'ordering': ['created_at'],
            },
        ),
    ]
