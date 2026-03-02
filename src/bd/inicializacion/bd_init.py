import logging

from sqlalchemy import Engine, inspect, text
from sqlmodel import SQLModel

from src.config.engine_config import get_engine
from src.bd import schema  # noqa: F401

engine = get_engine()


def _ensure_live_new_columns(engine: Engine) -> None:
    inspector = inspect(engine)
    live_columns = {col["name"] for col in inspector.get_columns("live")} if "live" in inspector.get_table_names() else set()
    with engine.begin() as conn:
        if "drive_file_id" not in live_columns:
            conn.execute(text("ALTER TABLE live ADD COLUMN drive_file_id TEXT"))
        if "content_hash" not in live_columns:
            conn.execute(text("ALTER TABLE live ADD COLUMN content_hash TEXT"))


def inicializar_bd_sqlite() -> Engine:
    logging.info("Inicializando base de datos SQLite")
    SQLModel.metadata.create_all(engine)
    _ensure_live_new_columns(engine)
    inspector = inspect(engine)
    logging.info("Tablas detectadas: %s", inspector.get_table_names())
    return engine
