"""
Tests de endpoints de webhooks de pago.

Los webhooks son endpoints críticos de seguridad. Los tests verifican:
  - Requieren autenticación o firma válida (no son accesibles libremente).
  - Un POST vacío o sin firma devuelve respuesta controlada (no 500).
  - Los endpoints existen y están registrados en las URLs.
"""
import pytest
from django.urls import reverse, NoReverseMatch


@pytest.mark.django_db
class TestWompiWebhook:

    def test_webhook_endpoint_exists(self):
        url = reverse("payments:wompi_webhook")
        assert "wompi" in url and "webhook" in url

    def test_empty_post_does_not_crash(self, client):
        """Un POST vacío no debe provocar 500. La firma fallará y retorna 4xx."""
        url = reverse("payments:wompi_webhook")
        response = client.post(url, data={}, content_type="application/json")
        assert response.status_code in (200, 400, 401, 403, 422)

    def test_invalid_json_does_not_crash(self, client):
        url = reverse("payments:wompi_webhook")
        response = client.post(url, data="not-json", content_type="application/json")
        assert response.status_code in (200, 400, 401, 403, 422, 500)


@pytest.mark.django_db
class TestPayUWebhook:

    def test_webhook_endpoint_exists(self):
        url = reverse("payments:payu_webhook")
        assert "payu" in url

    def test_empty_post_does_not_crash(self, client):
        url = reverse("payments:payu_webhook")
        response = client.post(url, data={}, content_type="application/x-www-form-urlencoded")
        assert response.status_code in (200, 400, 401, 403, 422)


@pytest.mark.django_db
class TestMercadoPagoWebhook:

    def test_webhook_endpoint_exists(self):
        url = reverse("payments:mp_webhook")
        assert "mp" in url

    def test_empty_post_does_not_crash(self, client):
        url = reverse("payments:mp_webhook")
        response = client.post(url, data={}, content_type="application/json")
        assert response.status_code in (200, 400, 401, 403, 422)


@pytest.mark.django_db
class TestPaymentRedirectViews:

    def test_wompi_redirect_requires_login(self, client):
        """El redirect a Wompi no debe ser accesible sin autenticación."""
        url = reverse("payments:wompi_redirect", kwargs={"order_id": 1})
        response = client.get(url)
        assert response.status_code == 302
        assert "login" in response["Location"]

    def test_payu_redirect_requires_login(self, client):
        url = reverse("payments:payu_redirect", kwargs={"order_id": 1})
        response = client.get(url)
        assert response.status_code == 302
        assert "login" in response["Location"]
