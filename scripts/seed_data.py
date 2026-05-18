# beauty_shop/scripts/seed_data.py

import os
import django
import random
from faker import Faker

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.catalog.models import Category, Brand, Product  # Asegúrate de que estos modelos existen y están migrados

fake = Faker()

def seed_categories():
    categories = ['Ropa', 'Accesorios', 'Belleza', 'Zapatos', 'Maquillaje']
    for name in categories:
        Category.objects.get_or_create(name=name)

def seed_brands():
    brands = ['Marca A', 'Marca B', 'Marca C']
    for name in brands:
        Brand.objects.get_or_create(name=name)

def seed_products(num=20):
    categories = list(Category.objects.all())
    brands = list(Brand.objects.all())

    for _ in range(num):
        Product.objects.create(
            name=fake.sentence(nb_words=3),
            description=fake.paragraph(),
            price=round(random.uniform(10, 200), 2),
            stock=random.randint(5, 100),
            category=random.choice(categories),
            brand=random.choice(brands),
        )

if __name__ == '__main__':
    print("⏳ Sembrando datos iniciales...")
    seed_categories()
    seed_brands()
    seed_products()
    print("✅ Datos sembrados exitosamente.")
