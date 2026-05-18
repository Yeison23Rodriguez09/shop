# beauty_shop/apps/core/views.py
from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.core.mail import send_mail, BadHeaderError
from django.conf import settings
from django.http import HttpResponse
from django.utils.html import strip_tags


class HomeView(View):
    def get(self, request):
        from django.db.models import Q
        from apps.catalog.models import Product

        base = Product.objects.filter(is_active=True).select_related('category')

        # Preferir ítems con imagen (image_url poblado o archivo subido).
        with_img = list(
            base.exclude(Q(image_url__isnull=True) | Q(image_url=''))
                .order_by('?')[:6]
        )
        # Si hay muy pocos con imagen, completar con cualquiera (sin duplicar).
        if len(with_img) < 3:
            featured = list(base.order_by('?')[:6])
        else:
            featured = with_img

        return render(request, 'core/home.html', {'featured_items': featured})


class AboutView(View):
    def get(self, request):
        return render(request, 'core/about.html')


class ContactView(View):
    def get(self, request):
        return render(request, 'core/contact.html')

    def post(self, request):
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        message = request.POST.get('message', '').strip()

        if not name or not email or not message:
            messages.error(request, "Por favor, completa todos los campos.")
            return redirect('core:contact')

        subject = f"Mensaje de contacto de {name}"
        clean_message = strip_tags(message)

        full_message = f"De: {name} <{email}>\n\n{clean_message}"

        try:
            send_mail(
                subject=subject,
                message=full_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.CONTACT_EMAIL],
                fail_silently=False,
            )
            messages.success(request, "Gracias por contactarnos. Te responderemos pronto.")
        except BadHeaderError:
            messages.error(request, "Encabezado inválido detectado.")
        except Exception:
            messages.error(request, "Error al enviar el mensaje. Intenta más tarde.")

        return redirect('core:contact')


# --- OPCIONAL ---
# Vista para monitoreo de estado del sistema
class HealthCheckView(View):
    def get(self, request):
        return HttpResponse("OK", content_type="text/plain")


# Vista para modo mantenimiento
class MaintenanceView(View):
    def get(self, request):
        return render(request, 'core/maintenance.html', status=503)
