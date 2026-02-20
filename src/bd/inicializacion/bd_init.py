import logging

from sqlalchemy import Engine, text, inspect
from sqlmodel import SQLModel

from src.config.engine_config import get_engine

engine = get_engine()

#si se cambia la base de datos crear otro metodo
#para inicializarse
def inicializar_bd_sqlite() -> Engine:
    logging.info("Inicializando base de datos SQLite")

    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS EJECUTIVO (
                NOMBRE TEXT NOT NULL,
                ESTADO TEXT NOT NULL,
                EPS TEXT NOT NULL
            );
        """))

    logging.info(f"Base de datos inicializada correctamente")

    return engine
