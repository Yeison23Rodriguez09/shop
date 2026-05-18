from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser, UserProfile

COLOMBIAN_DEPARTMENTS = [
    ('', 'Seleccionar departamento'),
    ('Amazonas', 'Amazonas'), ('Antioquia', 'Antioquia'), ('Arauca', 'Arauca'),
    ('Atlántico', 'Atlántico'), ('Bolívar', 'Bolívar'), ('Boyacá', 'Boyacá'),
    ('Caldas', 'Caldas'), ('Caquetá', 'Caquetá'), ('Casanare', 'Casanare'),
    ('Cauca', 'Cauca'), ('Cesar', 'Cesar'), ('Chocó', 'Chocó'),
    ('Córdoba', 'Córdoba'), ('Cundinamarca', 'Cundinamarca'), ('Guainía', 'Guainía'),
    ('Guaviare', 'Guaviare'), ('Huila', 'Huila'), ('La Guajira', 'La Guajira'),
    ('Magdalena', 'Magdalena'), ('Meta', 'Meta'), ('Nariño', 'Nariño'),
    ('Norte de Santander', 'Norte de Santander'), ('Putumayo', 'Putumayo'),
    ('Quindío', 'Quindío'), ('Risaralda', 'Risaralda'),
    ('San Andrés y Providencia', 'San Andrés y Providencia'),
    ('Santander', 'Santander'), ('Sucre', 'Sucre'), ('Tolima', 'Tolima'),
    ('Valle del Cauca', 'Valle del Cauca'), ('Vaupés', 'Vaupés'), ('Vichada', 'Vichada'),
    ('Bogotá D.C.', 'Bogotá D.C.'),
]

_FC = {'class': 'form-control'}
_FS = {'class': 'form-select'}


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={**_FC, 'placeholder': 'correo@ejemplo.com'})
    )

    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'username', 'password1', 'password2', 'role')
        widgets = {
            'first_name': forms.TextInput(attrs={**_FC, 'placeholder': 'Nombre'}),
            'last_name': forms.TextInput(attrs={**_FC, 'placeholder': 'Apellido'}),
            'username': forms.TextInput(attrs={**_FC, 'placeholder': 'Nombre de usuario'}),
            'role': forms.Select(attrs=_FC),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo ya está registrado.")
        return email


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={**_FC, 'placeholder': 'correo@ejemplo.com'})
    )
    password = forms.CharField(
        label='Contraseña',
        strip=False,
        widget=forms.PasswordInput(attrs={**_FC, 'placeholder': 'Contraseña'}),
    )

    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise forms.ValidationError("Esta cuenta está desactivada.", code='inactive')


class UserBasicForm(forms.ModelForm):
    """Nombre y apellido del CustomUser."""
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name')
        widgets = {
            'first_name': forms.TextInput(attrs={**_FC, 'placeholder': 'Nombre'}),
            'last_name': forms.TextInput(attrs={**_FC, 'placeholder': 'Apellido'}),
        }


class UserProfileForm(forms.ModelForm):
    """Campos del perfil extendido: contacto, documento, empresa y dirección."""
    department = forms.ChoiceField(
        choices=COLOMBIAN_DEPARTMENTS,
        required=False,
        label='Departamento',
        widget=forms.Select(attrs=_FS),
    )

    class Meta:
        model = UserProfile
        fields = (
            'phone', 'tipo_documento', 'numero_documento',
            'company_name', 'company_nit',
            'address_line1', 'address_line2', 'city', 'department', 'postal_code',
        )
        widgets = {
            'phone': forms.TextInput(attrs={**_FC, 'placeholder': 'Ej: 300 123 4567'}),
            'tipo_documento': forms.Select(attrs=_FS),
            'numero_documento': forms.TextInput(attrs={**_FC, 'placeholder': 'Número de documento'}),
            'company_name': forms.TextInput(attrs={**_FC, 'placeholder': 'Nombre de la empresa'}),
            'company_nit': forms.TextInput(attrs={**_FC, 'placeholder': 'NIT'}),
            'address_line1': forms.TextInput(attrs={**_FC, 'placeholder': 'Calle 45 # 12-30'}),
            'address_line2': forms.TextInput(attrs={**_FC, 'placeholder': 'Barrio, conjunto, apto…'}),
            'city': forms.TextInput(attrs={**_FC, 'placeholder': 'Ciudad'}),
            'postal_code': forms.TextInput(attrs={**_FC, 'placeholder': 'Código postal'}),
        }
