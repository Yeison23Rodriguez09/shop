# beauty_shop/apps/orders/tasks.py
from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from apps.orders.models import Order


@shared_task
def send_order_confirmation_email(order_id):
    try:
        order = Order.objects.get(pk=order_id)
        subject = f"Confirmación de tu pedido #{order.id}"
        to_email = order.user.email

        # Renderizar versión HTML y texto plano
        context = {'order': order}
        html_content = render_to_string('emails/order_confirmation.html', context)
        text_content = render_to_string('emails/order_confirmation.txt', context)

        # Crear y enviar email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()

        return f"Correo de confirmación enviado a {to_email}"

    except Order.DoesNotExist:
        return f"❌ Pedido con ID {order_id} no encontrado"
    except Exception as e:
        return f"⚠️ Error al enviar correo: {str(e)}"
