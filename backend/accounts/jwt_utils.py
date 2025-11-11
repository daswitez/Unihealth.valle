import os
import time
from typing import Any, Dict, Optional

import jwt
from django.conf import settings


def _get_jwt_secret() -> str:
    """
    Obtiene la clave para firmar JWT desde el entorno o fallback al SECRET_KEY.
    """
    return os.getenv("JWT_SECRET", settings.SECRET_KEY)


def _get_alg() -> str:
    return os.getenv("JWT_ALG", "HS256")


def _now_ts() -> int:
    return int(time.time())


def create_access_token(payload: Dict[str, Any], expires_in_seconds: int = 15 * 60) -> str:
    """
    Crea un access token con expiración corta.
    """
    claims = dict(payload)
    # PyJWT valida que 'sub' sea string; convertir si llega como int
    if "sub" in claims and not isinstance(claims["sub"], str):
        claims["sub"] = str(claims["sub"])
    claims["type"] = "access"
    claims["iat"] = _now_ts()
    claims["exp"] = _now_ts() + expires_in_seconds
    return jwt.encode(claims, _get_jwt_secret(), algorithm=_get_alg())


def create_refresh_token(payload: Dict[str, Any], expires_in_seconds: int = 7 * 24 * 60 * 60) -> str:
    """
    Crea un refresh token con expiración más larga.
    """
    claims = dict(payload)
    if "sub" in claims and not isinstance(claims["sub"], str):
        claims["sub"] = str(claims["sub"])
    claims["type"] = "refresh"
    claims["iat"] = _now_ts()
    claims["exp"] = _now_ts() + expires_in_seconds
    return jwt.encode(claims, _get_jwt_secret(), algorithm=_get_alg())


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decodifica y valida un token JWT. Devuelve claims o None si inválido/expirado.
    """
    try:
        return jwt.decode(token, _get_jwt_secret(), algorithms=[_get_alg()])
    except jwt.PyJWTError:
        return None

