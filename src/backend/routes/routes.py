import logging

from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["WABAPI"])

@router.get("/test", operation_id="Peticion_test", response_model=str)
def test() -> str:
    logging.info(f"Llega la peticion")
    return "Funciona"