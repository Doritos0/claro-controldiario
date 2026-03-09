from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import ExpiredSignatureError, InvalidTokenError
from pydantic import BaseModel

from src.backend.auth import create_access_token, create_refresh_token, verify_jwt
from src.bd.bd_usuario import UsuarioService

router = APIRouter(tags=["auth"])
_security = HTTPBearer(bearerFormat="JWT", auto_error=False)


class LoginRequest(BaseModel):
    user: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@router.post("/login", operation_id="Autenticar usuario", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    usuario_service = UsuarioService()
    usuario = usuario_service.autenticar(user=payload.user, password=payload.password)
    if not usuario:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    return LoginResponse(
        access_token=create_access_token(user=usuario.user, empresa_id=usuario.empresa_id),
        refresh_token=create_refresh_token(user=usuario.user, empresa_id=usuario.empresa_id),
    )


class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/refresh", operation_id="Refrescar access token", response_model=RefreshTokenResponse)
def refresh_token(credentials: HTTPAuthorizationCredentials | None = Depends(_security)) -> RefreshTokenResponse:
    try:
        if not credentials:
            raise ValueError("Bearer token faltante o inválido")

        payload = verify_jwt(authorization=f"Bearer {credentials.credentials}", is_refresh=True)
        return RefreshTokenResponse(
            access_token=create_access_token(user=payload["user"], empresa_id=payload["empresa_id"])
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except ExpiredSignatureError as e:
        raise HTTPException(status_code=401, detail="Token expirado") from e
    except InvalidTokenError as e:
        raise HTTPException(status_code=401, detail="Token inválido") from e
