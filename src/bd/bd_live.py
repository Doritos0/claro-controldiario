from src.bd.schema import LIVE

from sqlalchemy import Engine
from sqlmodel import Session, select
from pydantic import BaseModel

from src.config.engine_config import get_engine
from src.gemini.estructura import LIVERespuesta

class LIVEService():
    engine: Engine
    def __init__(self, engine: Engine | None = None):
        self.engine = engine or get_engine()

    def guardar_LIVE_metricas_sql(self, ejecutivo_id: int, metricas: LIVERespuesta):
        with Session(self.engine) as session:
            LIVE_nuevo = self.get_nuevo_LIVE_sql(ejecutivo_id=ejecutivo_id, fila=metricas)
            session.add(LIVE_nuevo)
            session.commit()
            session.refresh(LIVE_nuevo)
            return LIVE_nuevo

    @staticmethod
    def get_nuevo_LIVE_sql(ejecutivo_id: int, fila: LIVERespuesta) -> LIVE:
        return LIVE(
            ejecutivo_id=ejecutivo_id,
            fecha_live=fila.fecha_live,
            hora_inicio=fila.hora_inicio_live,
            duracion_live=fila.duracion_live,
            hora_termino=fila.hora_termino_live,
            visualizaciones=fila.visualizaciones,
            espectadores_unicos=fila.espectadores_unicos,
            espectadores_activos=fila.espectadores_activos,
            duracion_media_visualizacion=fila.duracion_media_visualizacion,
            pico_espectadores_simultaneos=fila.pico_espectadores_simultaneos
        )