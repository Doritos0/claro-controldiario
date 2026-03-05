import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.bd.bd_ejecutivo import EjecutivoService

router = APIRouter(tags=["web"])

@router.get("/test", operation_id="Peticion_test", response_model=str)
def test() -> str:
    logging.info(f"Llega la peticion")
    return "Funciona"

class EjecutivoRest(BaseModel):
    id: int | None
    nombre: str
    estado: str #EnumEstado
    eps: str #PHOENIX
    empresa_id: int

@router.post("/ejecutivos", operation_id="crear_ejecutivo", tags=["web"], response_model=int)
def crear_ejecutivo(payload: EjecutivoRest) -> int:
    ejecutivo_service = EjecutivoService()
    ejecutivo_creado = ejecutivo_service.guardar_ejecutivo_sql(nombre=payload.nombre,
                                                               estado=payload.estado,
                                                               eps=payload.eps,
                                                               empresa_id=payload.empresa_id)
    assert ejecutivo_creado is not None
    return ejecutivo_creado.id