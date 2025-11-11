from unittest import mock

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from django.db import connection

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
    """
    Pruebas de endpoints de autenticación (login, refresh, register, me).

    Nota: Para las pruebas de registro se requiere la presencia de tablas base
    (esquema app, roles, usuarios). Creamos dichas tablas con SQL mínimo en
    setUpClass para no depender de migraciones en el runner de tests.
    """

    # DDL mínimo para soportar registro y validaciones
    DDL = """
    CREATE SCHEMA IF NOT EXISTS app;

    CREATE TABLE IF NOT EXISTS app.roles (
      id BIGSERIAL PRIMARY KEY,
      nombre VARCHAR(32) NOT NULL UNIQUE
    );
    ALTER TABLE app.roles ADD COLUMN IF NOT EXISTS descripcion TEXT;

    CREATE TABLE IF NOT EXISTS app.usuarios (
      id BIGSERIAL PRIMARY KEY,
      email VARCHAR(254) NOT NULL UNIQUE,
      pass_hash TEXT NOT NULL,
      rol_id BIGINT NOT NULL REFERENCES app.roles(id),
      activo BOOLEAN NOT NULL DEFAULT TRUE,
      creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      actualizado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      ultimo_login TIMESTAMPTZ
    );

    INSERT INTO app.roles (nombre) VALUES ('user') ON CONFLICT (nombre) DO NOTHING;
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Crear esquema y tablas requeridas para tests de registro
        with connection.cursor() as cursor:
            cursor.execute(cls.DDL)

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

    def test_register_success_default_role(self):
        """
        Debe registrar un usuario con rol por defecto 'user' y devolver tokens.
        """
        url = reverse("auth-register")
        res = self.client.post(
            url,
            {"email": "new.user@example.com", "password": "StrongPass#1"},
            format="json",
        )
        self.assertEqual(res.status_code, 201)
        self.assertIn("access_token", res.data)
        self.assertIn("refresh_token", res.data)
        self.assertEqual(res.data["user"]["email"], "new.user@example.com")
        self.assertEqual(res.data["user"]["rol"], "user")

    def test_register_invalid_role(self):
        """
        Si el rol no existe, debe responder 400 (validador de serializer).
        """
        url = reverse("auth-register")
        res = self.client.post(
            url,
            {"email": "bad.role@example.com", "password": "StrongPass#1", "role": "nope"},
            format="json",
        )
        self.assertEqual(res.status_code, 400)

    def test_register_duplicate_email(self):
        """
        Si el email ya existe, debe responder 400 (validador de serializer).
        """
        url = reverse("auth-register")
        payload = {"email": "dup@example.com", "password": "StrongPass#1"}
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, 201)
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, 400)

