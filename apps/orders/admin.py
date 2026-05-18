from django.contrib import admin
from .models import Order, OrderItem, OrderLog


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_name', 'product_model', 'unit_price', 'quantity', 'subtotal')
    fields = ('product_name', 'product_model', 'quantity', 'unit_price', 'subtotal')

    def subtotal(self, obj):
        return f'${obj.subtotal:,.0f}'
    subtotal.short_description = 'Subtotal'


class OrderLogInline(admin.TabularInline):
    model = OrderLog
    extra = 0
    readonly_fields = ('previous_status', 'new_status', 'changed_by', 'note', 'source', 'created_at')
    fields = ('created_at', 'previous_status', 'new_status', 'source', 'changed_by', 'note')
    ordering = ('created_at',)
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'reference', 'user', 'status', 'payment_method',
        'total_price', 'created_at',
    )
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('reference', 'user__email', 'shipping_name', 'shipping_phone')
    readonly_fields = ('reference', 'created_at', 'updated_at', 'subtotal', 'total_price')
    ordering = ('-created_at',)
    inlines = [OrderItemInline, OrderLogInline]

    fieldsets = (
        ('Identificación', {
            'fields': ('reference', 'user', 'status', 'payment_method', 'payment_id', 'paid_at')
        }),
        ('Totales', {
            'fields': ('subtotal', 'shipping_cost', 'total_price')
        }),
        ('Dirección de entrega', {
            'fields': (
                'shipping_name', 'shipping_phone', 'shipping_address',
                'shipping_city', 'shipping_department', 'shipping_postal_code',
                'shipping_notes',
            )
        }),
        ('Notas internas', {
            'fields': ('internal_notes',),
            'classes': ('collapse',),
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def save_model(self, request, obj, form, change):
        """Registra log cuando el admin cambia el estado."""
        if change:
            old = Order.objects.get(pk=obj.pk)
            if old.status != obj.status:
                super().save_model(request, obj, form, change)
                from apps.orders.services.order_service import OrderService
                OrderService.change_status(
                    obj, obj.status,
                    changed_by=request.user,
                    note='Cambio realizado desde el panel de administración.',
                    source='admin',
                )
                return
        super().save_model(request, obj, form, change)


@admin.register(OrderLog)
class OrderLogAdmin(admin.ModelAdmin):
    list_display = ('order', 'previous_status', 'new_status', 'source', 'changed_by', 'created_at')
    list_filter = ('source', 'new_status', 'created_at')
    search_fields = ('order__reference', 'order__user__email', 'note')
    readonly_fields = ('order', 'previous_status', 'new_status', 'changed_by', 'note', 'source', 'created_at')
    ordering = ('-created_at',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
