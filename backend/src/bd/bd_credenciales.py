from src.bd.schema import Credenciales, Ejecutivo
from sqlalchemy import Engine, select
from sqlmodel import Session

from src.config.engine_config import get_engine

class CredencialesService:
    def __init__(self, engine: Engine | None = None):
        self.engine = engine or get_engine()

    def get_credenciales_sql(self, empresa_id: int) -> list[Credenciales]:
        with Session(self.engine) as session:
            stmt = (
                select(
                    Credenciales
                )
                .join(Ejecutivo, Ejecutivo.id == Credenciales.usuario_id)
                .where(Ejecutivo.empresa_id == empresa_id)
            )
            credenciales_list: list[Credenciales] = session.exec(stmt).scalars().all()
            
            return list(credenciales_list)

    def guardar_credenciales_sql(self, usuario_id: int, login_user: str, login_pass: str) -> Credenciales:
        with Session(self.engine) as session:
            crendenciales_existen = session.exec(select(Credenciales).where(Credenciales.usuario_id == usuario_id)).scalars().first()
            if crendenciales_existen:
                return Credenciales.model_validate(crendenciales_existen)
            credenciales = Credenciales(usuario_id=usuario_id, login_user=login_user, login_pass=login_pass)
            session.add(credenciales)
            session.commit()
            session.refresh(credenciales)
            return credenciales