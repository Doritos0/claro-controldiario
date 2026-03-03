from sqlalchemy import Engine, func, select
from sqlmodel import Session

from src.config.engine_config import get_engine
from src.bd.schema import Usuario


class UsuarioService:
    def __init__(self, engine: Engine | None = None):
        self.engine = engine or get_engine()

    def autenticar(self, user: str, password: str) -> Usuario | None:
        with Session(self.engine) as session:
            return session.exec(
                select(Usuario).where(
                    func.lower(Usuario.user) == user.lower(),
                    Usuario.password == password,
                )
            ).scalars().first()

    def guardar_usuario_sql(self, empresa_id: int, user: str, password: str) -> Usuario:
        with Session(self.engine) as session:
            usuario = session.exec(select(Usuario).where(func.lower(Usuario.user) == user.lower())).scalars().first()
            if usuario:
                return Usuario.model_validate(usuario)
            usuario = Usuario(empresa_id=empresa_id, user=user, password=password)
            session.add(usuario)
            session.commit()
            session.refresh(usuario)
            return usuario

    def get_usuarios_sql(self) -> list[Usuario]:
        with Session(self.engine) as session:
            return list(session.exec(select(Usuario)).scalars().all())
