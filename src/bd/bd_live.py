from datetime import datetime, time
import logging

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
    def parse_time_string(time_str: str | None) -> time | None:
        """Convierte formatos como '15:16', '15:16:00' o '1h 30m' a objeto time."""
        if not time_str or time_str == "null":
            return None
        
        # Si ya es un objeto time (por si acaso), devolverlo
        if isinstance(time_str, time):
            return time_str

        # Limpiar el string
        time_str = time_str.strip().lower()

        formats = ["%H:%M:%S", "%H:%M", "%I:%M %p"]
        for fmt in formats:
            try:
                return datetime.strptime(time_str, fmt).time()
            except ValueError:
                continue
        
        # Si es una duración tipo "47 min" o "1 h 3 min"
        # Esto es un fallback simple, puedes mejorarlo si es necesario
        try:
            if "min" in time_str:
                m = int(time_str.split("min")[0].strip().split()[-1])
                h = 0
                if "h" in time_str:
                    h = int(time_str.split("h")[0].strip())
                return time(hour=h, minute=m)
        except:
            pass

        logging.warning(f"No se pudo convertir el tiempo: {time_str}")
        return None

    def guardar_LIVE_metricas_sql(self, ejecutivo_id: int, metricas: LIVERespuesta):
        with Session(self.engine) as session:
            # Aquí aplicamos la conversión
            LIVE_nuevo = LIVE(
                ejecutivo_id=ejecutivo_id,
                fecha_live=metricas.fecha_live,
                hora_inicio=self.parse_time_string(metricas.hora_inicio_live),
                duracion_live=self.parse_time_string(metricas.duracion_live),
                hora_termino=self.parse_time_string(metricas.hora_termino_live),
                visualizaciones=metricas.visualizaciones,
                espectadores_unicos=metricas.espectadores_unicos,
                espectadores_activos=metricas.espectadores_activos,
                duracion_media_visualizacion=self.parse_time_string(metricas.duracion_media_visualizacion),
                pico_espectadores_simultaneos=metricas.pico_espectadores_simultaneos
            )
            session.add(LIVE_nuevo)
            session.commit()
            session.refresh(LIVE_nuevo)
            return LIVE_nuevo