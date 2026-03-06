from io import BytesIO
import json
import logging
from dotenv import load_dotenv
import os
from pathlib import Path
from dataclasses import dataclass
from pathlib import Path

from src.bd.bd_ejecutivo import EjecutivoService
from src.bd.bd_live import LIVEService
from src.bd.schema import Ejecutivo
from src.gemini.estructura import LIVERespuesta
from src.config.log_config import configurar_log
from src.gemini.gemini_ocr_service import GeminiOCRService
from src.reportes.dashboard_diario_service import DashboardDiarioService, resolver_fecha_objetivo


def ejecutar_proceso(empresa_id: int, fecha_objetivo: str | None = None, consolidado: str | None = None) -> list[LIVERespuesta]:
    configurar_log()
    load_dotenv()

    if fecha_objetivo is None:
        fecha_objetivo = resolver_fecha_objetivo(fecha_objetivo)
    try:
        BASE_DIR = Path(__file__).resolve().parent.parent
        gemini_service = GeminiOCRService()
        live_service = LIVEService()
        ejecutivo_service = EjecutivoService()
        ruta_descargas = BASE_DIR / "whatsapp-service" / "descargas" / fecha_objetivo
        extensiones = ['*.png', '*.jpg', '*.jpeg', '*.webp']
        imagenes = []

        ejecutivos = ejecutivo_service.get_ejecutivos_sql(empresa_id)
        dict_ejecutivos = {e.nro_telefono: e for e in ejecutivos if e.nro_telefono}

        if ruta_descargas.exists():
            for ext in extensiones:
                imagenes.extend(list(ruta_descargas.glob(ext)))
        else:
            logging.warning(f"La carpeta de imagenes no existe: {ruta_descargas}")
            imagenes=[]

        logging.info(f"Se encontraron {len(imagenes)} para la fecha {fecha_objetivo}")

        for imagen in imagenes:
            logging.info(f"Se esta procesando {imagen.name}")

            identificadores = imagen.name.split('_')

            numero_tel = identificadores[1]

            ejecutivo = dict_ejecutivos.get(numero_tel)

            if not ejecutivo:
                logging.warning(f"Número {numero_tel} no registrado en BD. Saltando...")
                continue

            with open(imagen, "rb") as f:
                imagen_bytes = f.read()

            res = gemini_service.get_respuesta_ocr(
                image_bytes=imagen_bytes,
                filename=imagen.name
            )
            try:
                live_service.guardar_LIVE_metricas_sql(ejecutivo.id, imagen.name, res)
                logging.info(f"Imagen de {ejecutivo.nombre} ingresada correctamente, filename {imagen}")
            except Exception as e:
                logging.warning(f"Error ingresando LIVE desde {imagen}")
                pass

    except Exception as e:
        logging.error(f"Error al ejecutar proceso: {e}")

if __name__ == "__main__":
    ejecutar_proceso(1, "06-03-2026")