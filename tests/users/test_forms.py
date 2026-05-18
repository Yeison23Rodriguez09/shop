"""
Tests de formularios de usuario: creación y validaciones de dominio.
"""
import pytest
from django.contrib.auth import get_user_model

from apps.users.forms import CustomUserCreationForm

User = get_user_model()


@pytest.mark.django_db
class TestCustomUserCreationForm:

    def _valid_data(self, email="form_test@example.com"):
        return {
            "first_name": "Test",
            "last_name": "User",
            "email": email,
            "username": email.split("@")[0],
            "password1": "SecureTestPass!1",
            "password2": "SecureTestPass!1",
            "role": "customer",
        }

    def test_valid_form_is_valid(self):
        form = CustomUserCreationForm(data=self._valid_data())
        assert form.is_valid(), form.errors

    def test_mismatched_passwords_invalid(self):
        data = self._valid_data()
        data["password2"] = "DifferentPass!9"
        form = CustomUserCreationForm(data=data)
        assert not form.is_valid()
        assert "password2" in form.errors

    def test_duplicate_email_raises_validation_error(self, user):
        data = self._valid_data(email=user.email)
        form = CustomUserCreationForm(data=data)
        assert not form.is_valid()
        assert "email" in form.errors

    def test_missing_email_is_invalid(self):
        data = self._valid_data()
        data["email"] = ""
        form = CustomUserCreationForm(data=data)
        assert not form.is_valid()
        assert "email" in form.errors
