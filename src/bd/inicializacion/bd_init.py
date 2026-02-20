import logging

from sqlalchemy import Engine, text, inspect
from sqlmodel import SQLModel

from src.config.engine_config import get_engine

from src.bd import schema

engine = get_engine()

#si se cambia la base de datos crear otro metodo
#para inicializarse
def inicializar_bd_sqlite() -> Engine:
    logging.info("Inicializando base de datos SQLite")
    SQLModel.metadata.create_all(engine)
    logging.info(f"Tablas creadas correctamente")
