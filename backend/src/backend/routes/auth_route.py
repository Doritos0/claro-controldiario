from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import ExpiredSignatureError, InvalidTokenError
from pydantic import BaseModel

from src.backend.auth import create_access_token, create_refresh_token, verify_jwt, refresh_access_token
from src.bd.bd_usuario import UsuarioService

router = APIRouter(tags=["auth"])
_security = HTTPBearer(bearerFormat="JWT", auto_error=False)


class LoginRequest(BaseModel):
    user: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str | None = None

@router.post("/login", operation_id="Autenticar usuario", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    usuario_service = UsuarioService()
    if not payload.user or not payload.password:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    
    return usuario_service.autenticar(payload.user, payload.password)


@router.post("/refresh", operation_id="Refrescar access token", response_model=RefreshResponse)
def refresh_token(payload: RefreshRequest) -> RefreshResponse:
    return refresh_access_token(payload.refresh_token)
