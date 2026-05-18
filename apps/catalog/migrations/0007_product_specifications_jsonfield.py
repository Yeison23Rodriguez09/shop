"""
Convierte Product.specifications de TextField a JSONField(default=dict).

Paso 1 (RunPython): normaliza los valores existentes mientras la columna
aún es texto: '' / espacios / JSON inválido -> '{}'. Los JSON válidos se
dejan tal cual (siguen siendo texto válido para json.loads).

Paso 2 (AlterField): cambia el campo a JSONField. Tras esto, todos los
valores son JSON parseable, así que el acceso vía ORM no rompe.
"""
import json
from django.db import migrations, models


def normalize_specs_forward(apps, schema_editor):
    Product = apps.get_model('catalog', 'Product')
    for pk, raw in Product.objects.values_list('pk', 'specifications'):
        fixed = '{}'
        if isinstance(raw, str) and raw.strip():
            try:
                parsed = json.loads(raw)
                fixed = raw if isinstance(parsed, dict) else '{}'
            except (ValueError, TypeError):
                fixed = '{}'
        elif isinstance(raw, dict):
            fixed = json.dumps(raw)
        if fixed != raw:
            Product.objects.filter(pk=pk).update(specifications=fixed)


def normalize_specs_backward(apps, schema_editor):
    """Reversa: serializa el dict a texto JSON."""
    Product = apps.get_model('catalog', 'Product')
    for pk, raw in Product.objects.values_list('pk', 'specifications'):
        if isinstance(raw, (dict, list)):
            Product.objects.filter(pk=pk).update(specifications=json.dumps(raw))


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0006_product_item_type_product_specifications_and_more'),
    ]

    operations = [
        migrations.RunPython(normalize_specs_forward, normalize_specs_backward),
        migrations.AlterField(
            model_name='product',
            name='specifications',
            field=models.JSONField(
                blank=True, default=dict,
                help_text='Especificaciones técnicas (dict JSON). '
                          'Ej: {"resolución": "4K", "garantía": "12 meses"}',
                verbose_name='Especificaciones',
            ),
        ),
    ]
