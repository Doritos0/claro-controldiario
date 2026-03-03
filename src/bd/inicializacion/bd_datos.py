import logging

from sqlalchemy import func, select
from sqlmodel import Session

from src.bd.bd_ejecutivo import EjecutivoService
from src.bd.schema import Empresa
from src.config.engine_config import get_engine


def _get_or_create_empresa(nombre: str) -> Empresa:
    engine = get_engine()
    with Session(engine) as session:
        empresa = session.exec(select(Empresa).where(func.lower(Empresa.nombre) == nombre.lower())).scalars().first()
        if empresa:
            return empresa

        empresa = Empresa(nombre=nombre)
        session.add(empresa)
        session.commit()
        session.refresh(empresa)
        return empresa


def inicializar_datos():
    empresa_claro = _get_or_create_empresa("Claro")
    _get_or_create_empresa("WOM")

    ejecutivo_service = EjecutivoService()
    daniela_baeza = ejecutivo_service.guardar_ejecutivo_sql("Daniela Baeza", "ACTIVO", "PHOENIX", empresa_claro.id).id
    assert daniela_baeza is not None
    ada_rengifo = ejecutivo_service.guardar_ejecutivo_sql("Ada Rengifo", "ACTIVO", "PHOENIX", empresa_claro.id).id
    assert ada_rengifo is not None
    barbara_cruz = ejecutivo_service.guardar_ejecutivo_sql("Bárbara Cruz", "ACTIVO", "PHOENIX", empresa_claro.id).id
    assert barbara_cruz is not None
    paulina_cataldo = ejecutivo_service.guardar_ejecutivo_sql("Paulina Cataldo", "ACTIVO", "PHOENIX", empresa_claro.id).id
    assert paulina_cataldo is not None
    rafael_cayun = ejecutivo_service.guardar_ejecutivo_sql("Rafael Cayun", "ACTIVO", "PHOENIX", empresa_claro.id).id
    assert rafael_cayun is not None
    tania_alviar = ejecutivo_service.guardar_ejecutivo_sql("Tania Alviar", "ACTIVO", "PHOENIX", empresa_claro.id).id
    assert tania_alviar is not None
    blanca_flores = ejecutivo_service.guardar_ejecutivo_sql("Blanca Flores", "ACTIVO", "PHOENIX", empresa_claro.id).id
    assert blanca_flores is not None
    isi_pastenes = ejecutivo_service.guardar_ejecutivo_sql("Isi Pastenes", "ACTIVO", "PHOENIX", empresa_claro.id).id
    assert isi_pastenes is not None
    logging.info("Base de datos inicializada con empresas y ejecutivos por defecto")
