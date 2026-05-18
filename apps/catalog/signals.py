# beauty_shop\apps\catalog\signals.py
from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from django.utils.text import slugify
from .models import Product, Category


@receiver(pre_save, sender=Category)
def auto_slug_category(sender, instance, **kwargs):
    if not instance.slug:
        instance.slug = slugify(instance.name)


@receiver(pre_save, sender=Product)
def auto_slug_product(sender, instance, **kwargs):
    if not instance.slug:
        instance.slug = slugify(instance.name)


@receiver(post_delete, sender=Product)
def delete_image_on_product_delete(sender, instance, **kwargs):
    """
    Borra la imagen del producto del sistema de archivos
    cuando el producto es eliminado.
    """
    if instance.image:
        instance.image.delete(save=False)
