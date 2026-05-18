"""
cancel_expired_orders — cancela ordenes 'pending' antiguas y libera su stock.

Pensado para correrse periodicamente (cron / Render Cron Job / scheduler):

    python manage.py cancel_expired_orders --hours 48
    python manage.py cancel_expired_orders --hours 48 --dry-run
    python manage.py cancel_expired_orders --hours 24 --methods wompi,payu,mercadopago

Reglas:
  - Solo afecta ordenes en estado 'pending'.
  - Por defecto NO toca metodos manuales ('transfer', 'cash') porque esos
    pueden estar legitimamente esperando confirmacion offline (transferencia
    bancaria que tarda dias). Pasalos via --methods si quieres incluirlos.
  - Usa OrderService.change_status('cancelled', ...) para que la reposicion
    de stock siga la misma logica idempotente que admin manual.
  - Reporta conteo y referencias afectadas.
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.orders.models import Order
from apps.orders.services.order_service import OrderService


DEFAULT_GATEWAY_METHODS = ('wompi', 'payu', 'mercadopago')


class Command(BaseCommand):
    help = "Cancela ordenes 'pending' antiguas y libera el stock reservado."

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours', type=int, default=48,
            help='Antiguedad minima en horas (default: 48).',
        )
        parser.add_argument(
            '--methods', type=str, default=','.join(DEFAULT_GATEWAY_METHODS),
            help='Metodos a afectar, separados por coma. Default: solo gateways.',
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Solo muestra que ordenes serian canceladas, no escribe.',
        )

    def handle(self, *args, **options):
        hours = options['hours']
        methods = [m.strip() for m in options['methods'].split(',') if m.strip()]
        dry_run = options['dry_run']

        cutoff = timezone.now() - timedelta(hours=hours)
        qs = (Order.objects
              .filter(status='pending', created_at__lt=cutoff,
                      payment_method__in=methods)
              .order_by('created_at'))

        total = qs.count()
        if total == 0:
            self.stdout.write(self.style.SUCCESS(
                f'No hay ordenes pending de mas de {hours}h en metodos {methods}.'
            ))
            return

        self.stdout.write(self.style.HTTP_INFO(
            f'Encontradas {total} ordenes pending > {hours}h en metodos {methods}.'
        ))
        if dry_run:
            for o in qs:
                self.stdout.write(
                    f'  [dry-run] {o.reference} | user={o.user.email} | '
                    f'creada={o.created_at:%Y-%m-%d %H:%M} | total={o.total_price}'
                )
            self.stdout.write(self.style.WARNING('** DRY RUN — no se escribio nada **'))
            return

        cancelled = 0
        for o in qs:
            OrderService.change_status(
                o, 'cancelled',
                source='system_expired',
                note=f'Cancelada automaticamente: pending > {hours}h sin confirmar pago.',
            )
            cancelled += 1
            self.stdout.write(self.style.SUCCESS(
                f'  cancelada {o.reference} (stock repuesto)'
            ))

        self.stdout.write(self.style.SUCCESS(
            f'OK: {cancelled} ordenes canceladas, stock repuesto.'
        ))
