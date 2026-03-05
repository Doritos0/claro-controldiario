from sqlalchemy import Engine, select
from sqlmodel import Session

from src.bd.schema import Configuracion
from src.config.engine_config import get_engine


class ConfiguracionService:
    def __init__(self, engine: Engine | None = None):
        self.engine = engine or get_engine()

    def get_por_usuario(self, usuario_id: int) -> Configuracion | None:
        with Session(self.engine) as session:
            return session.exec(select(Configuracion).where(Configuracion.usuario_id == usuario_id)).scalars().first()

    def upsert(self, usuario_id: int, grupo_wsp: str) -> Configuracion:
        with Session(self.engine) as session:
            configuracion = session.exec(select(Configuracion).where(Configuracion.usuario_id == usuario_id)).scalars().first()
            if configuracion:
                configuracion.grupo_wsp = grupo_wsp
            else:
                configuracion = Configuracion(usuario_id=usuario_id, grupo_wsp=grupo_wsp)
                session.add(configuracion)
            session.commit()
            session.refresh(configuracion)
            return configuracion
