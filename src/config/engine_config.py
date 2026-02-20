import logging

from functools import lru_cache
from os import environ

from sqlalchemy import Engine, create_engine

def _get_engine_sqlite():
    bd_name = environ.get("BD_NAME")
    assert bd_name is not None, "La variables de entorno BD_NAME no está definida"
    url = f"sqlite:///{bd_name}.db"
    return create_engine(url, connect_args={"check_same_thread": False})

def _get_engine():
    ambiente = environ.get("AMBIENTE","")
    logging.info(f"Ambiente que llega {ambiente}")
    if ambiente == "sqlite":
        return _get_engine_sqlite()
    else:
        raise ValueError(f"Ambiente invalido: {ambiente}")
    
@lru_cache(maxsize=1)
def get_engine() -> Engine:
    return _get_engine()