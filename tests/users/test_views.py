"""
Tests de vistas de usuarios: control de acceso y respuestas HTTP.
"""
import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestProfileViewAccess:

    def test_profile_requires_login(self, client):
        url = reverse("users:profile")
        response = client.get(url)
        # Django redirige al login cuando no está autenticado
        assert response.status_code == 302
        assert "/login" in response["Location"] or "/accounts" in response["Location"]

    def test_profile_accessible_when_logged_in(self, authenticated_client):
        url = reverse("users:profile")
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_profile_shows_user_email(self, authenticated_client, user):
        url = reverse("users:profile")
        response = authenticated_client.get(url)
        assert user.email.encode() in response.content


@pytest.mark.django_db
class TestOrderListAccess:

    def test_order_list_requires_login(self, client):
        url = reverse("orders:order_list")
        response = client.get(url)
        assert response.status_code == 302

    def test_order_list_accessible_when_logged_in(self, authenticated_client):
        url = reverse("orders:order_list")
        response = authenticated_client.get(url)
        assert response.status_code == 200
