import os
import sys
import logging
from pathlib import Path

from dotenv import load_dotenv

# Importamos tus servicios
from src.bd.schema import Ejecutivo
from src.drive.drive_imagenes import DriveImagenesService
from src.gemini.gemini_ocr_service import GeminiOCRService
from src.bd.bd_live import LIVEService
from src.config.log_config import configurar_log
from src.reportes.dashboard_diario_service import (
    DashboardDiarioService,
    resolver_fecha_objetivo,
)


def _load_runtime_env() -> Path | None:
    """
    Carga .env desde ubicaciones compatibles con ejecución local y PyInstaller.
    """
    candidate_paths: list[Path] = []

    if getattr(sys, "frozen", False):
        candidate_paths.append(Path(sys.executable).resolve().parent / ".env")

    candidate_paths.extend(
        [
            Path.cwd() / ".env",
            Path(__file__).resolve().parents[1] / ".env",
        ]
    )

    for env_path in candidate_paths:
        if env_path.exists():
            load_dotenv(env_path)
            return env_path

    load_dotenv()
    return None


def _resolve_credentials_path(raw_path: str | None, env_path: Path | None) -> str | None:
    if not raw_path:
        return None

    path = Path(raw_path)
    if path.is_absolute() and path.exists():
        return str(path)

    candidate_paths = [Path.cwd() / path]

    if env_path is not None:
        candidate_paths.append(env_path.parent / path)

    if getattr(sys, "frozen", False):
        candidate_paths.append(Path(sys.executable).resolve().parent / path)

    candidate_paths.append(Path(__file__).resolve().parents[1] / path)

    for candidate in candidate_paths:
        if candidate.exists():
            return str(candidate.resolve())

    return str(path)


def ejecutar_proceso_ocr(fecha_objetivo: str | None = None, full_scan: bool = False):
    """
    Orquestador que descarga imágenes de Drive y las procesa con Gemini OCR.
    """
    configurar_log()
    env_path = _load_runtime_env()

    credentials_path = _resolve_credentials_path(os.getenv("GOOGLE_DRIVE_CREDENTIALS_PATH"), env_path)
    root_folder_id = os.getenv("GOOGLE_DRIVE_ROOT_FOLDER_ID")

    if not credentials_path or not root_folder_id:
        logging.error(
            "Faltan variables de entorno. Asegura GOOGLE_DRIVE_CREDENTIALS_PATH y GOOGLE_DRIVE_ROOT_FOLDER_ID en el .env"
        )
        return None

    if not Path(credentials_path).exists():
        logging.error("No existe el archivo de credenciales en la ruta: %s", credentials_path)
        return None

    try:
        fecha_dashboard = resolver_fecha_objetivo(fecha_objetivo)

        logging.info("Inicializando servicios de Drive y Gemini...")
        drive_service = DriveImagenesService(credentials_path, root_folder_id)
        ocr_service = GeminiOCRService()
        live_service = LIVEService()
        dashboard_service = DashboardDiarioService()

        logging.info(f"Buscando imágenes para la fecha: {fecha_objetivo or 'Ayer (default)'}")
        imagenes_descargadas = drive_service.obtener_imagenes(fecha_objetivo, full_scan)

        if not imagenes_descargadas:
            logging.warning("No se encontraron imágenes para procesar.")
        else:
            logging.info(f"Se encontraron {len(imagenes_descargadas)} imágenes. Iniciando OCR...")

            for item in imagenes_descargadas:
                ejecutivo: Ejecutivo = item['ejecutivo']
                filename = item['filename']
                image_bytes = item['data']

                logging.info(f"--- Procesando: {filename} (Ejecutivo: {ejecutivo}) ---")

                resultado = ocr_service.get_respuesta_ocr(image_bytes, filename)
                live_service.guardar_LIVE_metricas_sql(ejecutivo.id, filename, resultado)

                print(f"\nRESULTADO PARA {ejecutivo} ({filename}):")
                print("-" * 40)
                print(resultado)
                print("-" * 40 + "\n")

        dashboard_path = dashboard_service.generar_dashboard_diario(fecha_dashboard)
        if dashboard_path:
            print(f"Dashboard diario generado: {dashboard_path}")
        else:
            print("No se pudo generar dashboard diario: no hay datos LIVE para la fecha objetivo.")

        return dashboard_path

    except Exception as e:
        logging.error(f"Error crítico en el proceso: {e}")
        return None


if __name__ == "__main__":
    ejecutar_proceso_ocr("02/03/26")
