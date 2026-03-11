from sqlalchemy import Engine, func, select
from sqlmodel import Session

from src.bd.schema import Ejecutivo

from src.config.engine_config import get_engine


class EjecutivoService:
    def __init__(self, engine: Engine | None = None):
        self.engine = engine or get_engine()

    def guardar_ejecutivo_sql(self, nombre: str, estado: str, eps: str, empresa_id: int, nro_telefono: int = 0) -> Ejecutivo:
        with Session(self.engine) as session:
            ejecutivo_existe = session.exec(
                select(Ejecutivo).where(
                    func.lower(Ejecutivo.nombre) == nombre.lower(),
                    Ejecutivo.empresa_id == empresa_id,
                    Ejecutivo.estado != "ELIMINADO",
                )
            ).scalars().first()
            if ejecutivo_existe:
                return Ejecutivo.model_validate(ejecutivo_existe)

            ejecutivo = Ejecutivo(empresa_id=empresa_id, nombre=nombre, estado=estado, eps=eps, nro_telefono=nro_telefono)
            session.add(ejecutivo)
            session.commit()
            session.refresh(ejecutivo)
            return ejecutivo

    def get_ejecutivos_sql(self, empresa_id: int | None = None, incluir_eliminados: bool = False) -> list[Ejecutivo]:
        with Session(self.engine) as session:
            statement = select(Ejecutivo)
            if empresa_id is not None:
                statement = statement.where(Ejecutivo.empresa_id == empresa_id)
            if not incluir_eliminados:
                statement = statement.where(func.lower(Ejecutivo.estado) != "eliminado")
            ejecutivos = session.exec(statement).scalars().all()
            return list(ejecutivos)

    def modificar_ejecutivo_sql(self, ejecutivo_id: int, empresa_id: int, estado: str, nro_telefono: int) -> Ejecutivo | None:
        with Session(self.engine) as session:
            ejecutivo = session.exec(
                select(Ejecutivo).where(Ejecutivo.id == ejecutivo_id, Ejecutivo.empresa_id == empresa_id)
            ).scalars().first()

            if not ejecutivo:
                return None

            ejecutivo.estado = estado
            ejecutivo.nro_telefono = nro_telefono
            session.add(ejecutivo)
            session.commit()
            session.refresh(ejecutivo)
            return ejecutivo

    def eliminar_ejecutivo_sql(self, ejecutivo_id: int, empresa_id: int) -> Ejecutivo | None:
        with Session(self.engine) as session:
            ejecutivo = session.exec(
                select(Ejecutivo).where(Ejecutivo.id == ejecutivo_id, Ejecutivo.empresa_id == empresa_id)
            ).scalars().first()

            if not ejecutivo:
                return None

            ejecutivo.estado = "ELIMINADO"
            session.add(ejecutivo)
            session.commit()
            session.refresh(ejecutivo)
            return ejecutivo
