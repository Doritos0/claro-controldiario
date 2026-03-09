from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jwt import ExpiredSignatureError, InvalidTokenError

SECRET_KEY = "controlDiario"
REFRESH_KEY = "controlDiarioRefresh"
PASSWORD_SECRET = "passwordSecret"
ALGORITHM = "HS256"


ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

_password_hasher = PasswordHasher()


def _with_pepper(password: str) -> str:
    return f"{password}{PASSWORD_SECRET}"


def hash_password(password: str) -> str:
    return _password_hasher.hash(_with_pepper(password))


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return _password_hasher.verify(hashed_password, _with_pepper(password))
    except VerifyMismatchError:
        return False


def create_access_token(user: str, empresa_id: int):
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        
        "iat" : int(now.timestamp()),
        "sub": user,
        "empresa_id": empresa_id,
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token, expire


def create_refresh_token(user: str, empresa_id: int):
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user,
        "empresa_id": empresa_id,
        "type": "refresh",
        "exp": expire,
    }
    token = jwt.encode(payload, REFRESH_KEY, algorithm=ALGORITHM)
    return token, expire


def verify_jwt(authorization: str, is_refresh: bool = False):
    if not authorization or not authorization.startswith("Bearer "):
        raise ValueError("Bearer token faltante o inválido")

    token = authorization.split(" ", 1)[1].strip()
    key = REFRESH_KEY if is_refresh else SECRET_KEY

    try:
        payload = jwt.decode(token, key, algorithms=[ALGORITHM])
        expected_type = "refresh" if is_refresh else "access"
        if payload.get("type") != expected_type:
            raise InvalidTokenError("Tipo de token inválido")
        return payload
    except ExpiredSignatureError as e:
        raise ExpiredSignatureError("Token expirado") from e
    except InvalidTokenError as e:
        raise InvalidTokenError("Token inválido") from e
    
def refresh_access_token(refresh_token: str):
    return _refresh_logic(refresh_token)


def _refresh_logic(refresh_token: str):
    try:
        decoded = jwt.decode(refresh_token, REFRESH_KEY, algorithms=[ALGORITHM])

        if decoded.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Token incorrecto")

        new_access_token, _ = create_access_token(
            decoded["sub"],
            decoded["empresa_id"],
        )

        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Refresh token inválido")
