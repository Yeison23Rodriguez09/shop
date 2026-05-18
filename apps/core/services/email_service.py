# beauty_shop\apps\core\services\email_service.py
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.conf import settings


def send_simple_email(subject, message, recipient_list, from_email=None):
    """
    Envía un correo de texto plano.
    """
    send_mail(
        subject=subject,
        message=message,
        from_email=from_email or settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_list,
        fail_silently=False,
    )


def send_html_email(subject, template_name, context, recipient_list, from_email=None):
    """
    Envía un correo con HTML renderizado desde una plantilla.
    """
    html_message = render_to_string(template_name, context)
    email = EmailMessage(
        subject=subject,
        body=html_message,
        from_email=from_email or settings.DEFAULT_FROM_EMAIL,
        to=recipient_list,
    )
    email.content_subtype = "html"  # Necesario para que el body sea interpretado como HTML
    email.send(fail_silently=False)
