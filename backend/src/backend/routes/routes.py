import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.bd.bd_ejecutivo import EjecutivoService
from src.proceso_01_ocr import ejecutar_proceso

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

class EjecutarRequest(BaseModel):
    empresa_id: int
    fecha_objetivo: str | None = None
    consolidado: str | None = None

@router.post("/ejecutar", operation_id="Ejecutar_reporte_diario", tags=["web"])
def ejecutar(payload: EjecutarRequest):
    return ejecutar_proceso(
        empresa_id=payload.empresa_id,
        fecha_objetivo=payload.fecha_objetivo,
        consolidado=payload.consolidado
    )