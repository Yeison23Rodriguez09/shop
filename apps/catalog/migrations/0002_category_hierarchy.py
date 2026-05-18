# Generated manually for Category hierarchy support
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0001_initial'),
    ]

    operations = [
        # Quitar el unique=True de name (multiples subcategorias pueden tener
        # el mismo nombre bajo distintos padres, ej "Sensores de movimiento")
        migrations.AlterField(
            model_name='category',
            name='name',
            field=models.CharField(max_length=100, verbose_name='Nombre'),
        ),
        # Campos nuevos
        migrations.AddField(
            model_name='category',
            name='parent',
            field=models.ForeignKey(
                blank=True,
                help_text='Si esta vacio, es categoria principal. Si tiene valor, es subcategoria.',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='children',
                to='catalog.category',
                verbose_name='Categoria padre',
            ),
        ),
        migrations.AddField(
            model_name='category',
            name='order',
            field=models.PositiveIntegerField(
                default=0,
                help_text='Orden de aparicion en menus y listados.',
                verbose_name='Orden',
            ),
        ),
        migrations.AddField(
            model_name='category',
            name='image_path',
            field=models.CharField(
                blank=True,
                help_text='Ruta relativa a la imagen de portada (ej: cctv/portada.jpg).',
                max_length=255,
                verbose_name='Ruta de imagen',
            ),
        ),
        migrations.AddField(
            model_name='category',
            name='is_active',
            field=models.BooleanField(
                default=True,
                help_text='Si esta desactivada, no se muestra al cliente.',
                verbose_name='Activa',
            ),
        ),
        migrations.AddField(
            model_name='category',
            name='source_path',
            field=models.CharField(
                blank=True,
                help_text='Ruta en content/ que origino esta categoria (auto-llenada por sync_content).',
                max_length=500,
                verbose_name='Ruta en disco',
            ),
        ),
        migrations.AddField(
            model_name='category',
            name='last_synced_at',
            field=models.DateTimeField(
                blank=True,
                help_text='Timestamp de la ultima vez que sync_content actualizo este registro.',
                null=True,
                verbose_name='Ultima sincronizacion',
            ),
        ),
        migrations.AlterModelOptions(
            name='category',
            options={
                'ordering': ['parent__name', 'order', 'name'],
                'verbose_name': 'Categoria',
                'verbose_name_plural': 'Categorias',
            },
        ),
    ]
