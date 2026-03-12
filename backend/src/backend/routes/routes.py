import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.responses import FileResponse
from jwt import ExpiredSignatureError, InvalidTokenError
from pydantic import BaseModel
import os
from src.backend.auth import verify_jwt, TokenStruct
from src.bd.bd_ejecutivo import EjecutivoService
from src.bd.bd_usuario import UsuarioService
from src.bd.bd_configuracion import ConfiguracionService
from src.bd.schema import LIVE, Configuracion
from src.proceso_01_ocr import ejecutar_proceso

_security = HTTPBearer(bearerFormat="JWT", auto_error=False)


def require_access_token(credentials: HTTPAuthorizationCredentials | None = Depends(_security)) -> dict:
    try:
        if not credentials:
            raise ValueError("Bearer token faltante o inválido")
        return verify_jwt(authorization=f"Bearer {credentials.credentials}", is_refresh=False)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except ExpiredSignatureError as e:
        raise HTTPException(status_code=401, detail="Token expirado") from e
    except InvalidTokenError as e:
        raise HTTPException(status_code=401, detail="Token inválido") from e


router = APIRouter(tags=["web"], dependencies=[Depends(require_access_token)])


@router.get("/test", operation_id="Peticion_test", response_model=str)
def test() -> str:
    logging.info("Llega la peticion")
    return "Funciona"


class RegisterRequest(BaseModel):
    empresa_id: int
    user: str
    password: str


class RegisterResponse(BaseModel):
    id: int
    empresa_id: int
    user: str


@router.post("/usuarios", operation_id="Registrar usuario", tags=["web"], response_model=RegisterResponse)
def registrar_usuario(payload: RegisterRequest) -> RegisterResponse:
    usuario_service = UsuarioService()
    usuario = usuario_service.guardar_usuario_sql(
        empresa_id=payload.empresa_id,
        user=payload.user,
        password=payload.password,
    )

    assert usuario.id is not None
    return RegisterResponse(id=usuario.id, empresa_id=usuario.empresa_id, user=usuario.user)


class EjecutivoRest(BaseModel):
    id: int | None = None
    nombre: str
    estado: str
    eps: str
    empresa_id: int | None = None
    nro_telefono: int


@router.post("/ejecutivos", operation_id="crear_ejecutivo", tags=["web"], response_model=int)
def crear_ejecutivo(payload: EjecutivoRest, token: TokenStruct = Depends(require_access_token)) -> int:
    ejecutivo_service = EjecutivoService()
    ejecutivo_creado = ejecutivo_service.guardar_ejecutivo_sql(
        nombre=payload.nombre,
        estado=payload.estado,
        eps=payload.eps,
        empresa_id=token.empresa_id,
        nro_telefono=payload.nro_telefono
    )
    assert ejecutivo_creado is not None
    return ejecutivo_creado.id


class EjecutarRequest(BaseModel):
    empresa_id: int | None = None
    fecha_objetivo: str | None = None
    consolidado: str | None = None

@router.post("/ejecutar", operation_id="Ejecutar_reporte_diario", tags=["web"])#, response_model=list[LIVE])
def ejecutar(payload: EjecutarRequest, token: TokenStruct = Depends(require_access_token)):# -> list[LIVE]:
    ruta_image = ejecutar_proceso(
        empresa_id=token.empresa_id,
        fecha_objetivo=payload.fecha_objetivo,
        consolidado=payload.consolidado,
    )

    if ruta_image is None or not os.path.exists(ruta_image):
            return []

    return FileResponse(ruta_image, media_type="image/png")


@router.post("/get_configuracion", operation_id="Obtener configuracion", tags=["web"], response_model=Configuracion | None)
def get_configuracion(token: TokenStruct = Depends(require_access_token)) -> Configuracion | None:
    configuracion_service = ConfiguracionService()
    return configuracion_service.get_configuracion(token.usuario_id)

class PostConfiguracionRequest(BaseModel):
    usuario_id: int | None = None
    grupo_wsp: str

@router.post("/post_configuracion", operation_id="Agregar configuracion", tags=["web"], response_model=Configuracion)
def post_configracion(payload: PostConfiguracionRequest, token: TokenStruct = Depends(require_access_token)) -> Configuracion:
    configuracion_service = ConfiguracionService()
    return configuracion_service.guardar_configuracion(usuario_id=token.usuario_id, grupo_wsp=payload.grupo_wsp)

class GetEjecutivosRequest(BaseModel):
    incluir_elimados: bool

@router.post("/get_ejecutivos", operation_id="Obtener ejecutivos", tags=["web"], response_model=list[EjecutivoRest])
def get_ejecutivos(payload: GetEjecutivosRequest, token: TokenStruct = Depends(require_access_token)) -> list[EjecutivoRest]:
    ejecutivo_service = EjecutivoService()
    return ejecutivo_service.get_ejecutivos_sql(
        empresa_id=token.empresa_id,
        incluir_eliminados=payload.incluir_elimados
    )

class ModificarEjecutivoRequest(BaseModel):
    ejecutivo_id: int
    nombre: str
    estado: str
    nro_telefono: int

@router.put("/modificar_ejecutivo", operation_id="Modificar ejecutivo", tags=["web"], response_model=EjecutivoRest | None)
def put_ejecutivo(payload: ModificarEjecutivoRequest, token : TokenStruct = Depends(require_access_token)) -> EjecutivoRest | None:
    ejecutivo_service = EjecutivoService()
    return ejecutivo_service.modificar_ejecutivo_sql(
        payload.ejecutivo_id,
        nombre=payload.nombre,
        estado=payload.estado,
        nro_telefono=payload.nro_telefono
    )

class EliminarEjecutivoRequest(BaseModel):
    ejecutivo_id: int

@router.put("/eliminar_ejecutivo", operation_id="Eliminar ejecutivo", tags=["web"], response_model=EjecutivoRest | None)
def eliminar_ejecutivo(payload: EliminarEjecutivoRequest, token : TokenStruct = Depends(require_access_token)) -> EjecutivoRest | None:
    ejecutivo_service = EjecutivoService()
    return ejecutivo_service.eliminar_ejecutivo_sql(payload.ejecutivo_id)