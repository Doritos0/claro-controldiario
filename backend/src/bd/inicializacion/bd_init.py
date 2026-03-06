import logging

from sqlalchemy import Engine, inspect, text
from sqlmodel import SQLModel

from src.config.engine_config import get_engine

from src.bd import schema

engine = get_engine()


def inicializar_bd_sqlite() -> Engine:
    logging.info("Inicializando base de datos SQLite")
    SQLModel.metadata.create_all(engine)

    with engine.begin() as conn:
        inspector = inspect(conn)
        tablas = inspector.get_table_names()

        if "empresa" not in tablas:
            conn.execute(text("CREATE TABLE empresa (id INTEGER PRIMARY KEY, nombre VARCHAR NOT NULL)"))

        if "usuario" not in tablas:
            conn.execute(text("CREATE TABLE usuario (id INTEGER PRIMARY KEY, empresa_id INTEGER NOT NULL, user VARCHAR NOT NULL, password VARCHAR NOT NULL)"))

        conn.execute(text("INSERT INTO empresa (nombre) SELECT 'Claro' WHERE NOT EXISTS (SELECT 1 FROM empresa WHERE lower(nombre)='claro')"))
        conn.execute(text("INSERT INTO empresa (nombre) SELECT 'WOM' WHERE NOT EXISTS (SELECT 1 FROM empresa WHERE lower(nombre)='wom')"))

        if "ejecutivo" in tablas:
            cols_ejecutivo = {col['name'] for col in inspector.get_columns("ejecutivo")}
            
            # 1. Tu corrección existente para empresa_id
            if "empresa_id" not in cols_ejecutivo:
                conn.execute(text("ALTER TABLE ejecutivo ADD COLUMN empresa_id INTEGER"))
            
            # 2. NUEVA CORRECCIÓN para nro_telefono
            if "nro_telefono" not in cols_ejecutivo:
                logging.info("Agregando columna nro_telefono a la tabla ejecutivo")
                conn.execute(text("ALTER TABLE ejecutivo ADD COLUMN nro_telefono VARCHAR"))

            conn.execute(
                text(
                    "UPDATE ejecutivo SET empresa_id = (SELECT id FROM empresa WHERE lower(nombre)='claro' LIMIT 1) "
                    "WHERE empresa_id IS NULL"
                )
            )

    logging.info("Tablas creadas/actualizadas correctamente")
    return engine
