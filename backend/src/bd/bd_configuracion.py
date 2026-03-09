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