from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.backend.auth import refresh_access_token
from src.bd.bd_usuario import UsuarioService

router = APIRouter(tags=["auth"])


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


@router.post("/login", operation_id="autenticar_usuario", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    usuario_service = UsuarioService()
    if not payload.user or not payload.password:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    auth_response = usuario_service.autenticar(payload.user, payload.password)
    return LoginResponse.model_validate(auth_response)


@router.post(
    "/refresh", operation_id="refrescar_access_token", response_model=RefreshResponse
)
def refresh_token(payload: RefreshRequest) -> RefreshResponse:
    refresh_response = refresh_access_token(payload.refresh_token)
    return RefreshResponse.model_validate(refresh_response)
