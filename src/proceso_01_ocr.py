import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path

from src.bd.bd_live import LIVEService
from src.bd.schema import Ejecutivo
from src.config.log_config import configurar_log
from src.drive.drive_imagenes import DriveImagenesService
from src.gemini.gemini_ocr_service import GeminiOCRService
from src.reportes.dashboard_diario_service import DashboardDiarioService, resolver_fecha_objetivo
from src.runtime_setup import bootstrap_runtime


@dataclass
class OCRExecutionResult:
    dashboard_path: Path | None
    message: str
    success: bool


def _load_app_config(app_home: Path) -> dict:
    cfg_path = app_home / "app_config.json"
    if not cfg_path.exists():
        return {}
    try:
        data = json.loads(cfg_path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        logging.exception("No se pudo leer app_config.json")
        return {}


def _resolve_runtime_config(app_home: Path) -> tuple[str | None, str | None]:
    cfg = _load_app_config(app_home)

    credentials_path_raw = os.getenv("GOOGLE_DRIVE_CREDENTIALS_PATH") or cfg.get("google_drive_credentials_path")
    root_folder_id = os.getenv("GOOGLE_DRIVE_ROOT_FOLDER_ID") or cfg.get("google_drive_root_folder_id")

    credentials_path = None
    if isinstance(credentials_path_raw, str) and credentials_path_raw.strip():
        path = Path(credentials_path_raw.strip())
        if path.is_absolute():
            credentials_path = str(path)
        else:
            credentials_path = str((app_home / path).resolve())

    return credentials_path, root_folder_id


def ejecutar_proceso_ocr_con_resultado(fecha_objetivo: str | None = None, full_scan: bool = False) -> OCRExecutionResult:
    app_home = bootstrap_runtime()
    configurar_log()

    credentials_path, root_folder_id = _resolve_runtime_config(app_home)

    if not root_folder_id:
        msg = (
            "Falta GOOGLE_DRIVE_ROOT_FOLDER_ID. Configúralo en app_config.json "
            f"ubicado en: {app_home / 'app_config.json'}"
        )
        logging.error(msg)
        return OCRExecutionResult(dashboard_path=None, message=msg, success=False)

    if not credentials_path or not Path(credentials_path).exists():
        msg = (
            "No se encontró credentials.json para Drive. "
            f"Ruta esperada: {credentials_path or (app_home / 'credentials.json')}"
        )
        logging.error(msg)
        return OCRExecutionResult(dashboard_path=None, message=msg, success=False)

    if not os.getenv("GEMINI_API_KEY"):
        msg = (
            "Falta GEMINI_API_KEY. Configúrala en app_config.json "
            f"ubicado en: {app_home / 'app_config.json'}"
        )
        logging.error(msg)
        return OCRExecutionResult(dashboard_path=None, message=msg, success=False)

    try:
        fecha_dashboard = resolver_fecha_objetivo(fecha_objetivo)

        drive_service = DriveImagenesService(credentials_path, root_folder_id)
        ocr_service = GeminiOCRService()
        live_service = LIVEService()
        dashboard_service = DashboardDiarioService(output_dir=str(app_home / "artifacts"))

        imagenes_descargadas = drive_service.obtener_imagenes(fecha_objetivo, full_scan)

        if imagenes_descargadas:
            for item in imagenes_descargadas:
                ejecutivo: Ejecutivo = item["ejecutivo"]
                filename = item["filename"]
                image_bytes = item["data"]
                resultado = ocr_service.get_respuesta_ocr(image_bytes, filename)
                live_service.guardar_LIVE_metricas_sql(ejecutivo.id, filename, resultado)

        dashboard_path = dashboard_service.generar_dashboard_diario(fecha_dashboard)
        if dashboard_path:
            return OCRExecutionResult(
                dashboard_path=dashboard_path,
                message=f"Dashboard diario generado: {dashboard_path}",
                success=True,
            )

        return OCRExecutionResult(
            dashboard_path=None,
            message=(
                "No se generó dashboard para la fecha objetivo. "
                "Verifica que existan carpetas/imágenes en Drive para esa fecha y que el root folder sea correcto."
            ),
            success=False,
        )

    except Exception as e:
        msg = f"Error crítico en el proceso OCR: {e}"
        logging.exception(msg)
        return OCRExecutionResult(dashboard_path=None, message=msg, success=False)


def ejecutar_proceso_ocr(fecha_objetivo: str | None = None, full_scan: bool = False):
    return ejecutar_proceso_ocr_con_resultado(fecha_objetivo=fecha_objetivo, full_scan=full_scan).dashboard_path


if __name__ == "__main__":
    home = bootstrap_runtime()
    print(f"App home: {home}")
    result = ejecutar_proceso_ocr_con_resultado("02/03/26")
    print(result.message)
