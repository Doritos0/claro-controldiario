import logging

from src.bd.bd_ejecutivo import EjecutivoService

def inicializar_datos():
    ejecutivo_service = EjecutivoService()
    daniela_baeza = ejecutivo_service.guardar_ejecutivo_sql("Daniela Baeza", "ACTIVO", "PHOENIX").id
    assert daniela_baeza is not None
    ada_rengifo = ejecutivo_service.guardar_ejecutivo_sql("Ada Rengifo", "ACTIVO", "PHOENIX").id
    assert ada_rengifo is not None
    barbara_cruz = ejecutivo_service.guardar_ejecutivo_sql("Bárbara Cruz", "ACTIVO", "PHOENIX").id
    assert barbara_cruz is not None
    paulina_cataldo = ejecutivo_service.guardar_ejecutivo_sql("Paulina Cataldo", "ACTIVO", "PHOENIX").id
    assert paulina_cataldo is not None
    rafael_cayun = ejecutivo_service.guardar_ejecutivo_sql("Rafael Cayun", "ACTIVO", "PHOENIX").id
    assert rafael_cayun is not None
    tania_alviar = ejecutivo_service.guardar_ejecutivo_sql("Tania Alviar", "ACTIVO", "PHOENIX").id
    assert tania_alviar is not None
    logging.info("Base de datos limpiada y clientes iniciales guardados")