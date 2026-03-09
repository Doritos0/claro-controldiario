from sqlalchemy import Engine, func, select
from sqlmodel import Session

from src.backend.auth import hash_password, verify_password
from src.config.engine_config import get_engine
from src.bd.schema import Usuario
from fastapi import HTTPException

from src.backend.auth import create_access_token, create_refresh_token


class UsuarioService:
    def __init__(self, engine: Engine | None = None):
        self.engine = engine or get_engine()

    def get_usuario_by_user(self, user: str) -> Usuario | None:
        with Session(self.engine) as session:
            return session.exec(
                select(Usuario).where(func.lower(Usuario.user) == user.lower())
            ).scalars().first()

    def autenticar(self, user: str, password: str) -> Usuario | None:
        usuario = self.get_usuario_by_user(user)

        if not usuario.password:
            raise HTTPException(status_code=401, detail="Usuario sin contraseña configurada")

        if not verify_password(password, usuario.password):
            raise HTTPException(status_code=401, detail="Credenciales invalidas")
        
        access_token, _ = create_access_token(usuario.user, usuario.empresa_id)
        refresh_token, _ = create_refresh_token(usuario.user, usuario.empresa_id)

        return {
            "access_token": access_token,
            "type": "bearer",
            "expires_in" : 60 * 60,
            "refresh_token" : refresh_token
        }

    def guardar_usuario_sql(self, empresa_id: int, user: str, password: str) -> Usuario:
        with Session(self.engine) as session:
            usuario = session.exec(select(Usuario).where(func.lower(Usuario.user) == user.lower())).scalars().first()
            if usuario:
                return Usuario.model_validate(usuario)

            usuario = Usuario(empresa_id=empresa_id, user=user, password=hash_password(password))
            session.add(usuario)
            session.commit()
            session.refresh(usuario)
            return usuario

    def get_usuarios_sql(self) -> list[Usuario]:
        with Session(self.engine) as session:
            return list(session.exec(select(Usuario)).scalars().all())
