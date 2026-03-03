import logging

from functools import lru_cache
from os import environ
from pathlib import Path

from sqlalchemy import Engine, create_engine


def _get_engine_sqlite() -> Engine:
    bd_path = environ.get("BD_PATH")
    if bd_path:
        db_file = Path(bd_path)
    else:
        bd_name = environ.get("BD_NAME", "CLARO-TIKTOK")
        db_file = Path(f"{bd_name}.db")

    db_file.parent.mkdir(parents=True, exist_ok=True)
    url = f"sqlite:///{db_file}"
    logging.info("Usando SQLite en: %s", db_file)
    return create_engine(url, connect_args={"check_same_thread": False})


def _get_engine() -> Engine:
    ambiente = environ.get("AMBIENTE", "sqlite").strip().lower()
    logging.info("Ambiente que llega %s", ambiente)

    if ambiente == "sqlite":
        return _get_engine_sqlite()

    raise ValueError(f"Ambiente invalido: {ambiente}")


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    return _get_engine()
