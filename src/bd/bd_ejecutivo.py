from sqlalchemy import Engine, func, select
from sqlmodel import Session

from src.bd.schema import Ejecutivo

from src.config.engine_config import get_engine

class EjecutivoService:
    def __init__(self, engine: Engine | None = None):
        self.engine = engine or get_engine()

    def guardar_ejecutivo_sql(self, nombre: str, estado: str, eps: str) -> Ejecutivo:
        with Session(self.engine) as session:
            ejecutivo_existe = session.exec(select(Ejecutivo).where(func.lower(Ejecutivo.nombre) == nombre.lower())).first()
            if ejecutivo_existe:
                return Ejecutivo.model_validate(ejecutivo_existe)
            ejecutivo = Ejecutivo(nombre=nombre, estado=estado, eps=eps)
            session.add(ejecutivo)
            session.commit()
            session.refresh(ejecutivo)
            return ejecutivo