from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jwt import ExpiredSignatureError, InvalidTokenError

SECRET_KEY = "controlDiario"
REFRESH_KEY = "controlDiarioRefresh"
PASSWORD_SECRET = "passwordSecret"
ALGORITHM = "HS256"

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


def create_access_token(user: str, empresa_id: int) -> str:
    payload = {
        "user": user,
        "empresa_id": empresa_id,
        "token_type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user: str, empresa_id: int) -> str:
    payload = {
        "user": user,
        "empresa_id": empresa_id,
        "token_type": "refresh",
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
    }
    return jwt.encode(payload, REFRESH_KEY, algorithm=ALGORITHM)


def verify_jwt(authorization: str, is_refresh: bool = False) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise ValueError("Bearer token faltante o inválido")

    token = authorization.split(" ", 1)[1].strip()
    key = REFRESH_KEY if is_refresh else SECRET_KEY

    try:
        payload = jwt.decode(token, key, algorithms=[ALGORITHM])
        expected_type = "refresh" if is_refresh else "access"
        if payload.get("token_type") != expected_type:
            raise InvalidTokenError("Tipo de token inválido")
        return payload
    except ExpiredSignatureError as e:
        raise ExpiredSignatureError("Token expirado") from e
    except InvalidTokenError as e:
        raise InvalidTokenError("Token inválido") from e
