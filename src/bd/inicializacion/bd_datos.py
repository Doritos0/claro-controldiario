import logging

from src.bd.bd_ejecutivo import EjecutivoService

def inicializar_datos():
    ejecutivo_service = EjecutivoService()
    daniela_baeza = ejecutivo_service.guardar_ejecutivo_sql("Daniela Baeza", "ACTIVO", "PHOENIX").id
    assert daniela_baeza is not None
    logging.info("Base de datos limpiada y clientes iniciales guardados")