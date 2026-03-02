from __future__ import annotations

from datetime import datetime, time
import hashlib
import logging

from sqlalchemy import Engine
from sqlmodel import Session, select

from src.bd.schema import LIVE
from src.config.engine_config import get_engine
from src.gemini.estructura import LIVERespuesta


class LIVEService:
    engine: Engine

    def __init__(self, engine: Engine | None = None):
        self.engine = engine or get_engine()

    def guardar_LIVE_metricas_sql(
        self,
        ejecutivo_id: int,
        nombre_captura: str,
        metricas: LIVERespuesta,
        drive_file_id: str | None = None,
        content_bytes: bytes | None = None,
    ):
        content_hash = hashlib.sha256(content_bytes).hexdigest() if content_bytes else None
        with Session(self.engine) as session:
            if drive_file_id:
                live = session.exec(select(LIVE).where(LIVE.drive_file_id == drive_file_id)).first()
                if live:
                    logging.debug("LIVE ya existe por drive_file_id")
                    return None
            if content_hash:
                live = session.exec(select(LIVE).where(LIVE.content_hash == content_hash)).first()
                if live:
                    logging.debug("LIVE ya existe por content_hash")
                    return None
            live = session.exec(select(LIVE).where(LIVE.nombre_captura == nombre_captura)).first()
            if live:
                logging.debug("LIVE ya ingresado por nombre_captura")
                return None

            live_nuevo = self.build_live_entity(
                ejecutivo_id=ejecutivo_id,
                nombre_captura=nombre_captura,
                metricas=metricas,
                drive_file_id=drive_file_id,
                content_hash=content_hash,
            )
            session.add(live_nuevo)
            session.commit()
            session.refresh(live_nuevo)
            return live_nuevo

    @staticmethod
    def parse_time_string(time_str: str | None) -> time | None:
        if not time_str or time_str == "null":
            return None
        if isinstance(time_str, time):
            return time_str

        value = time_str.strip().lower()
        for fmt in ["%H:%M:%S", "%H:%M", "%I:%M %p"]:
            try:
                return datetime.strptime(value, fmt).time()
            except ValueError:
                continue

        try:
            if "min" in value:
                m = int(value.split("min")[0].strip().split()[-1])
                h = int(value.split("h")[0].strip()) if "h" in value else 0
                return time(hour=h, minute=m)
        except Exception:  # noqa: BLE001
            pass

        logging.warning("No se pudo convertir el tiempo: %s", time_str)
        return None

    def build_live_entity(
        self,
        ejecutivo_id: int,
        nombre_captura: str,
        metricas: LIVERespuesta,
        drive_file_id: str | None,
        content_hash: str | None,
    ) -> LIVE:
        return LIVE(
            ejecutivo_id=ejecutivo_id,
            fecha_live=metricas.fecha_live,
            hora_inicio=self.parse_time_string(metricas.hora_inicio_live),
            duracion_live=self.parse_time_string(metricas.duracion_live),
            hora_termino=self.parse_time_string(metricas.hora_termino_live),
            visualizaciones=metricas.visualizaciones,
            espectadores_unicos=metricas.espectadores_unicos,
            espectadores_activos=metricas.espectadores_activos,
            duracion_media_visualizacion=self.parse_time_string(str(metricas.duracion_media_visualizacion) if metricas.duracion_media_visualizacion else None),
            pico_espectadores_simultaneos=metricas.pico_espectadores_simultaneos,
            nombre_captura=nombre_captura,
            drive_file_id=drive_file_id,
            content_hash=content_hash,
        )
