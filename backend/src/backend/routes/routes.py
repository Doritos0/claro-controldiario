import logging
import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import ExpiredSignatureError, InvalidTokenError
from pydantic import BaseModel

from src.backend.auth import TokenStruct, verify_jwt
from src.bd.bd_configuracion import ConfiguracionService
from src.bd.bd_ejecutivo import EjecutivoService
from src.bd.bd_usuario import UsuarioService
from src.bd.schema import Configuracion, LIVE
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


class UsuarioModificacionRequest(BaseModel):
    user: str | None = None
    password: str | None = None


@router.put("/usuarios/modificar", operation_id="Modificar usuario", tags=["web"], response_model=RegisterResponse)
def modificar_usuario(payload: UsuarioModificacionRequest, token: TokenStruct = Depends(require_access_token)) -> RegisterResponse:
    usuario_service = UsuarioService()
    usuario_modificado = usuario_service.modificar_usuario_sql(
        usuario_id=token.usuario_id,
        user=payload.user,
        password=payload.password,
    )

    if not usuario_modificado or usuario_modificado.id is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return RegisterResponse(id=usuario_modificado.id, empresa_id=usuario_modificado.empresa_id, user=usuario_modificado.user)


class EjecutivoRest(BaseModel):
    id: int | None = None
    nombre: str
    estado: str
    eps: str
    empresa_id: int | None = None
    nro_telefono: int


class EjecutivoModificacionRequest(BaseModel):
    estado: str
    nro_telefono: int


@router.post("/ejecutivos", operation_id="crear_ejecutivo", tags=["web"], response_model=int)
def crear_ejecutivo(payload: EjecutivoRest, token: TokenStruct = Depends(require_access_token)) -> int:
    ejecutivo_service = EjecutivoService()
    ejecutivo_creado = ejecutivo_service.guardar_ejecutivo_sql(
        nombre=payload.nombre,
        estado=payload.estado,
        eps=payload.eps,
        empresa_id=token.empresa_id,
        nro_telefono=payload.nro_telefono,
    )
    assert ejecutivo_creado is not None
    return ejecutivo_creado.id


@router.get("/ejecutivos", operation_id="listar_ejecutivos", tags=["web"], response_model=list[EjecutivoRest])
def listar_ejecutivos(token: TokenStruct = Depends(require_access_token)) -> list[EjecutivoRest]:
    ejecutivo_service = EjecutivoService()
    ejecutivos = ejecutivo_service.get_ejecutivos_sql(empresa_id=token.empresa_id, incluir_eliminados=False)
    return [
        EjecutivoRest(
            id=ejecutivo.id,
            nombre=ejecutivo.nombre,
            estado=ejecutivo.estado,
            eps=ejecutivo.eps,
            empresa_id=ejecutivo.empresa_id,
            nro_telefono=ejecutivo.nro_telefono,
        )
        for ejecutivo in ejecutivos
    ]


@router.put("/ejecutivos/{ejecutivo_id}", operation_id="modificar_ejecutivo", tags=["web"], response_model=EjecutivoRest)
def modificar_ejecutivo(ejecutivo_id: int, payload: EjecutivoModificacionRequest, token: TokenStruct = Depends(require_access_token)) -> EjecutivoRest:
    ejecutivo_service = EjecutivoService()
    ejecutivo_modificado = ejecutivo_service.modificar_ejecutivo_sql(
        ejecutivo_id=ejecutivo_id,
        empresa_id=token.empresa_id,
        estado=payload.estado,
        nro_telefono=payload.nro_telefono,
    )

    if not ejecutivo_modificado or ejecutivo_modificado.id is None:
        raise HTTPException(status_code=404, detail="Ejecutivo no encontrado")

    return EjecutivoRest(
        id=ejecutivo_modificado.id,
        nombre=ejecutivo_modificado.nombre,
        estado=ejecutivo_modificado.estado,
        eps=ejecutivo_modificado.eps,
        empresa_id=ejecutivo_modificado.empresa_id,
        nro_telefono=ejecutivo_modificado.nro_telefono,
    )


@router.patch("/ejecutivos/{ejecutivo_id}/eliminar", operation_id="eliminar_ejecutivo", tags=["web"], response_model=EjecutivoRest)
def eliminar_ejecutivo(ejecutivo_id: int, token: TokenStruct = Depends(require_access_token)) -> EjecutivoRest:
    ejecutivo_service = EjecutivoService()
    ejecutivo_eliminado = ejecutivo_service.eliminar_ejecutivo_sql(ejecutivo_id=ejecutivo_id, empresa_id=token.empresa_id)

    if not ejecutivo_eliminado or ejecutivo_eliminado.id is None:
        raise HTTPException(status_code=404, detail="Ejecutivo no encontrado")

    return EjecutivoRest(
        id=ejecutivo_eliminado.id,
        nombre=ejecutivo_eliminado.nombre,
        estado=ejecutivo_eliminado.estado,
        eps=ejecutivo_eliminado.eps,
        empresa_id=ejecutivo_eliminado.empresa_id,
        nro_telefono=ejecutivo_eliminado.nro_telefono,
    )


class EjecutarRequest(BaseModel):
    empresa_id: int | None = None
    fecha_objetivo: str | None = None
    consolidado: str | None = None


@router.post("/ejecutar", operation_id="Ejecutar_reporte_diario", tags=["web"])  # , response_model=list[LIVE])
def ejecutar(payload: EjecutarRequest, token: TokenStruct = Depends(require_access_token)):  # -> list[LIVE]:
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


@router.put("/configuracion/modificar", operation_id="Modificar configuracion", tags=["web"], response_model=Configuracion)
def modificar_configuracion(payload: PostConfiguracionRequest, token: TokenStruct = Depends(require_access_token)) -> Configuracion:
    configuracion_service = ConfiguracionService()
    return configuracion_service.modificar_configuracion(usuario_id=token.usuario_id, grupo_nuevo=payload.grupo_wsp)
