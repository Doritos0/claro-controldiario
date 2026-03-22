from datetime import datetime, time
import logging

from src.bd.schema import LIVE

from sqlalchemy import Engine
from sqlmodel import Session, select
from pydantic import BaseModel

from src.config.engine_config import get_engine
from src.gemini.estructura import LIVERespuesta


class LIVEService:
    engine: Engine

    def __init__(self, engine: Engine | None = None):
        self.engine = engine or get_engine()

    def guardar_LIVE_metricas_sql(
        self, ejecutivo_id: int, nombre_captura: str, metricas: LIVERespuesta
    ):
        live = self.get_LIVE_por_captura(nombre_captura)
        if live:
            logging.debug(f"LIVE ya ingresado")
            return live
        with Session(self.engine) as session:
            LIVE_nuevo = self.get_nuevo_LIVE_sql(
                ejecutivo_id=ejecutivo_id,
                nombre_captura=nombre_captura,
                metricas=metricas,
            )
            session.add(LIVE_nuevo)
            session.commit()
            session.refresh(LIVE_nuevo)
            return LIVE_nuevo

    def get_LIVE_por_captura(self, nombre_captura: str):
        with Session(self.engine) as session:
            live = session.exec(
                select(LIVE).where(LIVE.nombre_captura == nombre_captura)
            ).first()
            return live

    @staticmethod
    def parse_time_string(time_str: str | None) -> time | None:
        """Limpia y convierte strings de tiempo, manejando alucinaciones de Gemini."""
        if not time_str or str(time_str).lower() == "null":
            return None

        # 1. Limpieza de alucinaciones (ej: '00:00:14-26:00' -> '00:00:14')
        # Cortamos en el primer guion, espacio o signo de suma
        limpio = str(time_str).split("-")[0].split("+")[0].split(" ")[0].strip()

        # 2. Intentar formatos estándar
        formats = ["%H:%M:%S", "%H:%M", "%I:%M:%S %p", "%I:%M %p"]
        for fmt in formats:
            try:
                return datetime.strptime(limpio, fmt).time()
            except ValueError:
                continue

        # 3. Fallback para duraciones de TikTok (ej: "25 min", "1 h 2 min")
        try:
            time_str_low = str(time_str).lower()
            h, m, s = 0, 0, 0
            if "h" in time_str_low:
                h = int(time_str_low.split("h")[0].strip().split()[-1])
            if "min" in time_str_low:
                m = int(time_str_low.split("min")[0].strip().split()[-1])
            if "s" in time_str_low:
                s = int(time_str_low.split("s")[0].strip().split()[-1])

            if h or m or s:
                return time(hour=h % 24, minute=m % 60, second=s % 60)
        except:
            pass

        logging.warning(f"No se pudo parsear el tiempo tras limpieza: {time_str}")
        return None

    def get_nuevo_LIVE_sql(
        self, ejecutivo_id: int, nombre_captura: str, metricas: LIVERespuesta
    ):
        return LIVE(
            ejecutivo_id=ejecutivo_id,
            fecha_live=metricas.fecha_live,
            hora_inicio=self.parse_time_string(metricas.hora_inicio_live),
            duracion_live=self.parse_time_string(metricas.duracion_live),
            hora_termino=self.parse_time_string(metricas.hora_termino_live),
            visualizaciones=metricas.visualizaciones,
            espectadores_unicos=metricas.espectadores_unicos,
            espectadores_activos=metricas.espectadores_activos,
            duracion_media_visualizacion=self.parse_time_string(
                metricas.duracion_media_visualizacion
            ),
            pico_espectadores_simultaneos=metricas.pico_espectadores_simultaneos,
            nombre_captura=nombre_captura,
        )
