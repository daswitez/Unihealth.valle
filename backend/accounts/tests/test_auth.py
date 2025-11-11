from unittest import mock

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.jwt_utils import create_access_token, create_refresh_token, decode_token
from accounts.serializers import AuthResult


class JwtUtilsTests(TestCase):
    def test_access_and_refresh_tokens(self):
        claims = {"sub": 1, "email": "test@example.com", "role": "admin"}
        access = create_access_token(claims, expires_in_seconds=60)
        refresh = create_refresh_token(claims, expires_in_seconds=120)
        self.assertTrue(access)
        self.assertTrue(refresh)
        self.assertEqual(decode_token(access)["type"], "access")
        self.assertEqual(decode_token(refresh)["type"], "refresh")


class AuthViewsTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    @mock.patch("accounts.views.authenticate_user")
    def test_login_success(self, mock_auth):
        # Simula autenticación exitosa
        user = mock.Mock()
        user.id = 1
        user.email = "user@example.com"
        user.rol = mock.Mock()
        user.rol.nombre = "user"
        mock_auth.return_value = AuthResult(ok=True, user=user)

        url = reverse("auth-login")
        res = self.client.post(url, {"email": "user@example.com", "password": "secret"}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertIn("access_token", res.data)
        self.assertIn("refresh_token", res.data)
        self.assertIn("user", res.data)

    @mock.patch("accounts.views.authenticate_user")
    def test_login_failure(self, mock_auth):
        mock_auth.return_value = AuthResult(ok=False, user=None, error="Credenciales inválidas")
        url = reverse("auth-login")
        res = self.client.post(url, {"email": "bad@example.com", "password": "wrong"}, format="json")
        self.assertEqual(res.status_code, 401)

    def test_refresh_flow(self):
        claims = {"sub": 1, "email": "user@example.com", "role": "user"}
        refresh = create_refresh_token(claims, expires_in_seconds=60)
        url = reverse("auth-refresh")
        res = self.client.post(url, {"refresh_token": refresh}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertIn("access_token", res.data)

    def test_me_requires_auth(self):
        url = reverse("auth-me")
        res = self.client.get(url)
        # Sin credenciales, DRF responde 403 (Forbidden) con IsAuthenticated
        self.assertEqual(res.status_code, 403)

