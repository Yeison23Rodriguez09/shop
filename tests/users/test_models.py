"""
Tests de modelos de usuarios: CustomUser y UserProfile.

Verifica: email como campo de login, full_name, roles, y creación
automática de perfil mediante señal post_save.
"""
import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestCustomUserModel:

    def test_email_is_username_field(self):
        assert User.USERNAME_FIELD == "email"

    def test_create_user_with_email(self):
        u = User.objects.create_user(
            email="nuevo@example.com",
            password="SecurePass!1",
            username="nuevo",
        )
        assert u.email == "nuevo@example.com"
        assert u.check_password("SecurePass!1")

    def test_full_name_with_first_and_last(self):
        u = User(first_name="Ana", last_name="García", email="a@b.com")
        assert u.full_name == "Ana García"

    def test_full_name_falls_back_to_email(self):
        u = User(first_name="", last_name="", email="solo@email.com")
        assert u.full_name == "solo@email.com"

    def test_default_role_is_customer(self):
        u = User.objects.create_user(
            email="customer@example.com",
            password="Pass!1234",
            username="cust1",
        )
        assert u.role == User.Role.CUSTOMER

    def test_str_returns_email(self, user):
        assert str(user) == user.email

    def test_duplicate_email_raises(self, user):
        with pytest.raises(Exception):
            User.objects.create_user(
                email=user.email,  # mismo email
                password="OtherPass!1",
                username="duplicate",
            )


@pytest.mark.django_db
class TestUserProfileSignal:

    def test_profile_created_on_new_user(self):
        """El signal post_save debe crear UserProfile automáticamente."""
        from apps.users.models import UserProfile
        u = User.objects.create_user(
            email="profile_test@example.com",
            password="Pass!1234",
            username="profile_test",
        )
        assert UserProfile.objects.filter(user=u).exists()

    def test_profile_str_contains_user_email(self):
        from apps.users.models import UserProfile
        u = User.objects.create_user(
            email="str_test@example.com",
            password="Pass!1234",
            username="str_test",
        )
        profile = UserProfile.objects.get(user=u)
        assert u.email in str(profile)

    def test_profile_full_address_empty_by_default(self):
        from apps.users.models import UserProfile
        u = User.objects.create_user(
            email="addr_test@example.com",
            password="Pass!1234",
            username="addr_test",
        )
        profile = UserProfile.objects.get(user=u)
        assert profile.full_address == ""
