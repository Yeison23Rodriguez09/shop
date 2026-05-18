# beauty_shop\apps\core\services\pdf_service.py
import tempfile
from django.template.loader import render_to_string
from weasyprint import HTML, CSS
from django.conf import settings
from pathlib import Path


def generate_pdf_from_template(template_name, context, output_filename=None):
    """
    Genera un PDF desde una plantilla HTML.

    Args:
        template_name (str): Ruta de la plantilla HTML (ej: 'invoices/order_pdf.html').
        context (dict): Contexto para renderizar la plantilla.
        output_filename (str): Nombre del archivo (opcional). Si no se indica, se devuelve como binario.

    Returns:
        bytes si output_filename es None, o path completo del archivo generado.
    """
    html_string = render_to_string(template_name, context)
    html = HTML(string=html_string, base_url=settings.BASE_DIR)

    if output_filename:
        output_path = Path(settings.MEDIA_ROOT) / 'pdfs' / output_filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        html.write_pdf(target=str(output_path))
        return str(output_path)
    else:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as pdf_file:
            html.write_pdf(target=pdf_file.name)
            pdf_file.seek(0)
            return pdf_file.read()
