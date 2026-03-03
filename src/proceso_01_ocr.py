import os
import sys
import logging
from dataclasses import dataclass
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


@dataclass
class OCRExecutionResult:
    dashboard_path: Path | None
    message: str
    success: bool


def _load_runtime_env() -> tuple[Path | None, list[Path]]:
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
            return env_path, candidate_paths

    load_dotenv()
    return None, candidate_paths


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


def ejecutar_proceso_ocr_con_resultado(
    fecha_objetivo: str | None = None,
    full_scan: bool = False,
) -> OCRExecutionResult:
    """
    Orquestador que descarga imágenes de Drive y las procesa con Gemini OCR.
    Retorna un resultado detallado para consumo de UI.
    """
    configurar_log()
    env_path, env_candidates = _load_runtime_env()

    credentials_path = _resolve_credentials_path(os.getenv("GOOGLE_DRIVE_CREDENTIALS_PATH"), env_path)
    root_folder_id = os.getenv("GOOGLE_DRIVE_ROOT_FOLDER_ID")

    if not credentials_path or not root_folder_id:
        env_locations = " | ".join(str(p) for p in env_candidates)
        msg = (
            "Faltan variables de entorno requeridas (GOOGLE_DRIVE_CREDENTIALS_PATH / "
            "GOOGLE_DRIVE_ROOT_FOLDER_ID). "
            f".env encontrado: {env_path or 'NO'}. Rutas buscadas: {env_locations}"
        )
        logging.error(msg)
        return OCRExecutionResult(dashboard_path=None, message=msg, success=False)

    if not Path(credentials_path).exists():
        msg = f"No existe el archivo de credenciales en la ruta resuelta: {credentials_path}"
        logging.error(msg)
        return OCRExecutionResult(dashboard_path=None, message=msg, success=False)

    try:
        fecha_dashboard = resolver_fecha_objetivo(fecha_objetivo)

        logging.info("Inicializando servicios de Drive y Gemini...")
        drive_service = DriveImagenesService(credentials_path, root_folder_id)
        ocr_service = GeminiOCRService()
        live_service = LIVEService()
        dashboard_service = DashboardDiarioService()

        logging.info("Buscando imágenes para la fecha: %s", fecha_objetivo or "Ayer (default)")
        imagenes_descargadas = drive_service.obtener_imagenes(fecha_objetivo, full_scan)

        if not imagenes_descargadas:
            logging.warning("No se encontraron imágenes para procesar.")
        else:
            logging.info("Se encontraron %s imágenes. Iniciando OCR...", len(imagenes_descargadas))

            for item in imagenes_descargadas:
                ejecutivo: Ejecutivo = item["ejecutivo"]
                filename = item["filename"]
                image_bytes = item["data"]

                logging.info("--- Procesando: %s (Ejecutivo: %s) ---", filename, ejecutivo)

                resultado = ocr_service.get_respuesta_ocr(image_bytes, filename)
                live_service.guardar_LIVE_metricas_sql(ejecutivo.id, filename, resultado)

        dashboard_path = dashboard_service.generar_dashboard_diario(fecha_dashboard)
        if dashboard_path:
            msg = f"Dashboard diario generado: {dashboard_path}"
            return OCRExecutionResult(dashboard_path=dashboard_path, message=msg, success=True)

        msg = (
            "No se generó dashboard para la fecha objetivo. "
            "Puede que no existan imágenes/datos LIVE para ese día o que la carpeta no coincida en Drive."
        )
        logging.warning(msg)
        return OCRExecutionResult(dashboard_path=None, message=msg, success=False)

    except Exception as e:
        msg = f"Error crítico en el proceso OCR: {e}"
        logging.exception(msg)
        return OCRExecutionResult(dashboard_path=None, message=msg, success=False)


def ejecutar_proceso_ocr(fecha_objetivo: str | None = None, full_scan: bool = False):
    """Compatibilidad hacia atrás: retorna solo Path | None."""
    return ejecutar_proceso_ocr_con_resultado(fecha_objetivo=fecha_objetivo, full_scan=full_scan).dashboard_path


if __name__ == "__main__":
    result = ejecutar_proceso_ocr_con_resultado("02/03/26")
    print(result.message)
