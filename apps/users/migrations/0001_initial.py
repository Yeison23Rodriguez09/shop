import django.contrib.auth.models
import django.contrib.auth.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, verbose_name='superuser status')),
                ('username', models.CharField(
                    error_messages={'unique': 'A user with that username already exists.'},
                    help_text='Required. 150 characters or fewer.',
                    max_length=150,
                    unique=True,
                    validators=[django.contrib.auth.validators.UnicodeUsernameValidator()],
                    verbose_name='username',
                )),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('is_staff', models.BooleanField(default=False, verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='Correo electrónico')),
                ('role', models.CharField(
                    choices=[('customer', 'Cliente'), ('admin', 'Administrador')],
                    default='customer',
                    max_length=20,
                    verbose_name='Rol',
                )),
                ('groups', models.ManyToManyField(
                    blank=True,
                    related_name='customuser_groups',
                    related_query_name='user',
                    to='auth.group',
                    verbose_name='groups',
                )),
                ('user_permissions', models.ManyToManyField(
                    blank=True,
                    related_name='customuser_permissions',
                    related_query_name='user',
                    to='auth.permission',
                    verbose_name='user permissions',
                )),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone', models.CharField(blank=True, max_length=20, verbose_name='Teléfono / WhatsApp')),
                ('tipo_documento', models.CharField(
                    blank=True,
                    choices=[('CC', 'Cédula de Ciudadanía'), ('CE', 'Cédula de Extranjería'), ('NIT', 'NIT (empresa)'), ('PP', 'Pasaporte')],
                    default='CC',
                    max_length=5,
                    verbose_name='Tipo de documento',
                )),
                ('numero_documento', models.CharField(blank=True, max_length=30, verbose_name='Número de documento')),
                ('address_line1', models.CharField(blank=True, help_text='Ej: Calle 45 # 12-30, Apto 301', max_length=200, verbose_name='Dirección')),
                ('address_line2', models.CharField(blank=True, max_length=100, verbose_name='Barrio / Conjunto')),
                ('city', models.CharField(blank=True, max_length=100, verbose_name='Ciudad')),
                ('department', models.CharField(blank=True, max_length=100, verbose_name='Departamento')),
                ('postal_code', models.CharField(blank=True, max_length=10, verbose_name='Código postal')),
                ('company_name', models.CharField(blank=True, max_length=150, verbose_name='Empresa')),
                ('company_nit', models.CharField(blank=True, max_length=30, verbose_name='NIT empresa')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='profile',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Usuario',
                )),
            ],
            options={
                'verbose_name': 'Perfil de usuario',
                'verbose_name_plural': 'Perfiles de usuario',
            },
        ),
    ]
