import logging

from sqlalchemy import func, select
from sqlmodel import Session

from src.config.log_config import configurar_log

from src.bd.bd_ejecutivo import EjecutivoService
from src.bd.bd_usuario import UsuarioService
from src.bd.bd_credenciales import CredencialesService
from src.bd.schema import Empresa
from src.config.engine_config import get_engine

configurar_log()


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
    empresa_wom = _get_or_create_empresa("WOM")
    empresa_test = _get_or_create_empresa("TEST")

    usuario_service = UsuarioService()
    usuario_service.guardar_usuario_sql(empresa_id=empresa_claro.id, user="claro", password="claro123")
    usuario_service.guardar_usuario_sql(empresa_id=empresa_wom.id, user="wom", password="wom123")
    usuario_service.guardar_usuario_sql(empresa_id=empresa_test.id, user="TEST", password="12345")
    usuario_service.guardar_usuario_sql(empresa_id=empresa_test.id, user="TEST2", password="12345")
    usuario_service.guardar_usuario_sql(empresa_id=empresa_test.id, user="TEST3", password="12345")
    usuario_service.guardar_usuario_sql(empresa_id=empresa_claro.id, user="CLAROCORRECTO", password="12345")

    ejecutivo_service = EjecutivoService()
    daniela_baeza = ejecutivo_service.guardar_ejecutivo_sql("Daniela Baeza", "ACTIVO", "PHOENIX", empresa_claro.id, 0).id
    assert daniela_baeza is not None
    ada_rengifo = ejecutivo_service.guardar_ejecutivo_sql("Ada Rengifo", "ACTIVO", "PHOENIX", empresa_claro.id, 0).id
    assert ada_rengifo is not None
    barbara_cruz = ejecutivo_service.guardar_ejecutivo_sql("Bárbara Cruz", "ACTIVO", "PHOENIX", empresa_claro.id, 0).id
    assert barbara_cruz is not None
    paulina_cataldo = ejecutivo_service.guardar_ejecutivo_sql("Paulina Cataldo", "ACTIVO", "PHOENIX", empresa_claro.id, 0).id
    assert paulina_cataldo is not None
    rafael_cayun = ejecutivo_service.guardar_ejecutivo_sql("Rafael Cayun", "ACTIVO", "PHOENIX", empresa_claro.id, 0).id
    assert rafael_cayun is not None
    tania_alviar = ejecutivo_service.guardar_ejecutivo_sql("Tania Alviar", "ACTIVO", "PHOENIX", empresa_claro.id, 0).id
    assert tania_alviar is not None
    blanca_flores = ejecutivo_service.guardar_ejecutivo_sql("Blanca Flores", "ACTIVO", "PHOENIX", empresa_claro.id, 0).id
    assert blanca_flores is not None
    isi_pastenes = ejecutivo_service.guardar_ejecutivo_sql("Isi Pastenes", "ACTIVO", "PHOENIX", empresa_claro.id, 0).id
    assert isi_pastenes is not None
    thae_test = ejecutivo_service.guardar_ejecutivo_sql("Thae Test", "ACTIVO", "PHOENIX", empresa_claro.id, 56964587530).id
    assert thae_test is not None
    marselo = ejecutivo_service.guardar_ejecutivo_sql("Marcelo", "ACTIVO", "PHOENIX", empresa_claro.id, 56938912371).id
    assert marselo is not None

    credenciales_service = CredencialesService()
    daniela_credenciales = credenciales_service.guardar_credenciales_sql(usuario_id=daniela_baeza, login_user="199203444", login_pass="0LEZp7z0.xL5").id
    assert daniela_credenciales is not None
    ada_credenciales = credenciales_service.guardar_credenciales_sql(usuario_id=ada_rengifo, login_user="165787307", login_pass="Claro.2025").id
    assert ada_credenciales is not None
    barbara_credenciales = credenciales_service.guardar_credenciales_sql(usuario_id=barbara_cruz, login_user="146025986", login_pass="BAclaro-2026").id
    assert barbara_credenciales is not None
    rafa_credenciales = credenciales_service.guardar_credenciales_sql(usuario_id=rafael_cayun, login_user="190045846", login_pass="PJw9Kmw3).9U").id
    assert rafa_credenciales is not None
    pauli_credenciales = credenciales_service.guardar_credenciales_sql(usuario_id=paulina_cataldo, login_user="199203444", login_pass="9IsLb.m-M92V").id
    assert pauli_credenciales is not None
    tania_credenciales = credenciales_service.guardar_credenciales_sql(usuario_id=tania_alviar, login_user="171027306", login_pass="w8n,u56Fx#D.").id
    assert tania_credenciales is not None
    blanca_credenciales = credenciales_service.guardar_credenciales_sql(usuario_id=blanca_flores, login_user="211049251", login_pass="j|P8!csWQ;.P").id
    assert blanca_credenciales is not None
    isidora_credenciales = credenciales_service.guardar_credenciales_sql(usuario_id=isi_pastenes, login_user="199611933", login_pass="H,blxyx@(7sB").id
    assert isidora_credenciales is not None

    logging.info("Base de datos inicializada con empresas, usuarios y ejecutivos por defecto")
