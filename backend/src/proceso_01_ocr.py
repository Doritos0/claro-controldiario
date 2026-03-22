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
from src.bd.schema import Ejecutivo, LIVE
from src.gemini.estructura import LIVERespuesta
from src.config.log_config import configurar_log
from src.gemini.gemini_ocr_service import GeminiOCRService
from src.excelservice.excel_service import ExcelService
from src.frontservice.front_service import FrontService
from src.reportes.dashboard_diario_service import (
    DashboardDiarioService,
    resolver_fecha_objetivo,
)


class ProcesoService:
    @staticmethod
    def _normalizar_telefono(valor: str | int | None) -> str:
        if valor is None:
            return ""
        return "".join(ch for ch in str(valor) if ch.isdigit())

    @staticmethod
    def ejecutar_proceso(
        empresa_id: int,
        fecha_objetivo: str | None = None,
        consolidado: str | None = None,
    ) -> Path | None:
        load_dotenv()

        if fecha_objetivo is None:
            logging.info(f"Entra al if")
            fecha_objetivo = resolver_fecha_objetivo(fecha_objetivo)
            logging.info(f"fecha objetivo creada: {fecha_objetivo}")
        try:
            BASE_DIR = Path(__file__).resolve().parent.parent
            gemini_service = GeminiOCRService()
            live_service = LIVEService()
            ejecutivo_service = EjecutivoService()
            front_service = FrontService()
            excel_service = ExcelService()
            dashboard_service = DashboardDiarioService()
            ruta_descargas = (
                BASE_DIR / "whatsapp-service" / "descargas" / fecha_objetivo
            )
            logging.info(f"Ruta de imagenes {ruta_descargas}")
            extensiones = ["*.png", "*.jpg", "*.jpeg", "*.webp"]
            imagenes = []
            lives: list[LIVE] = []

            ejecutivos = ejecutivo_service.get_ejecutivos_sql(empresa_id)
            dict_ejecutivos = {
                ProcesoService._normalizar_telefono(e.nro_telefono): e
                for e in ejecutivos
                if e.nro_telefono
            }

            if ruta_descargas.exists():
                for ext in extensiones:
                    imagenes.extend(list(ruta_descargas.glob(ext)))
            else:
                logging.warning(f"La carpeta de imagenes no existe: {ruta_descargas}")
                imagenes = []

            logging.info(
                f"Se encontraron {len(imagenes)} para la fecha {fecha_objetivo}"
            )

            for imagen in imagenes:
                logging.info(f"Se esta procesando {imagen.name}")

                identificadores = imagen.name.split("_")
                if len(identificadores) < 3:
                    logging.warning(f"Nombre de archivo inválido: {imagen.name}")
                    continue

                numero_tel = ProcesoService._normalizar_telefono(identificadores[1])

                ejecutivo = dict_ejecutivos.get(numero_tel)

                if not ejecutivo:
                    logging.warning(
                        f"Número {numero_tel} no registrado en BD. Saltando..."
                    )
                    continue

                with open(imagen, "rb") as f:
                    imagen_bytes = f.read()

                res = gemini_service.get_respuesta_ocr(
                    image_bytes=imagen_bytes, filename=imagen.name
                )
                try:
                    ejecutivo_id = ejecutivo.id
                    if ejecutivo_id is None:
                        logging.warning(
                            f"Ejecutivo sin id para captura {imagen.name}. Saltando..."
                        )
                        continue
                    live = live_service.guardar_LIVE_metricas_sql(
                        ejecutivo_id, imagen.name, res
                    )
                    logging.info(
                        f"Imagen de {ejecutivo.nombre} ingresada correctamente, filename {imagen}"
                    )

                    lives.append(live)

                except Exception as e:
                    logging.warning(f"Error ingresando LIVE desde {imagen}")
                    pass

            # front_service.obtener_excel(empresa_id=empresa_id)
            excels = excel_service.procesar_excel()
            logging.info(f"Excels: {excels}")

            dashboard_path = dashboard_service.generar_dashboard_diario(
                fecha_objetivo=fecha_objetivo, empresa_id=empresa_id
            )
            return dashboard_path
        except Exception as e:
            logging.exception("Error al ejecutar proceso")
            raise
