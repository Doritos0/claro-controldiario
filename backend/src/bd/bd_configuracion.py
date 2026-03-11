from src.bd.schema import Configuracion

from sqlalchemy import Engine
from sqlmodel import Session, select

from src.config.engine_config import get_engine


class ConfiguracionService():
    engine: Engine

    def __init__(self, engine: Engine | None = None):
        self.engine = engine or get_engine()

    def get_configuracion(self, usuario_id: int) -> Configuracion | None:
        with Session(self.engine) as session:
            configuracion = session.exec(select(Configuracion).where(Configuracion.usuario_id == usuario_id)).first()
            return configuracion

    def guardar_configuracion(self, usuario_id: int, grupo_wsp: str) -> Configuracion:
        with Session(self.engine) as session:
            configuracion_existe = session.exec(select(Configuracion).where(Configuracion.usuario_id == usuario_id)).first()
            if configuracion_existe:
                configuracion_existe.grupo_wsp = grupo_wsp
                session.add(configuracion_existe)
                session.commit()
                session.refresh(configuracion_existe)
                return configuracion_existe

            configuracion = Configuracion(usuario_id=usuario_id, grupo_wsp=grupo_wsp)
            session.add(configuracion)
            session.commit()
            session.refresh(configuracion)
            return configuracion

    def modificar_configuracion(self, usuario_id: int, grupo_nuevo: str) -> Configuracion:
        with Session(self.engine) as session:
            configuracion = session.exec(select(Configuracion).where(Configuracion.usuario_id == usuario_id)).first()
            if not configuracion:
                configuracion = Configuracion(usuario_id=usuario_id, grupo_wsp=grupo_nuevo)
            else:
                configuracion.grupo_wsp = grupo_nuevo

            session.add(configuracion)
            session.commit()
            session.refresh(configuracion)
            return configuracion
