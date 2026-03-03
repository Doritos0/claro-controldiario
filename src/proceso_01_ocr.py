import json
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


@dataclass
class RuntimeConfig:
    credentials_path_raw: str | None
    root_folder_id: str | None


def _load_runtime_env() -> tuple[Path | None, list[Path]]:
    candidate_paths: list[Path] = []

    if getattr(sys, "frozen", False):
        candidate_paths.append(Path(sys.executable).resolve().parent / ".env")

    candidate_paths.extend([Path.cwd() / ".env", Path(__file__).resolve().parents[1] / ".env"])

    for env_path in candidate_paths:
        if env_path.exists():
            load_dotenv(env_path)
            return env_path, candidate_paths

    load_dotenv()
    return None, candidate_paths


def _load_runtime_config_file() -> tuple[dict, Path | None]:
    candidate_paths: list[Path] = []

    if getattr(sys, "frozen", False):
        candidate_paths.append(Path(sys.executable).resolve().parent / "app_config.json")

    candidate_paths.extend(
        [
            Path.cwd() / "app_config.json",
            Path(__file__).resolve().parents[1] / "app_config.json",
        ]
    )

    for cfg_path in candidate_paths:
        if cfg_path.exists():
            try:
                content = json.loads(cfg_path.read_text(encoding="utf-8"))
                return content if isinstance(content, dict) else {}, cfg_path
            except Exception:
                logging.exception("No se pudo leer app_config.json en %s", cfg_path)
                return {}, cfg_path

    return {}, None


def _resolve_runtime_config() -> tuple[RuntimeConfig, Path | None, list[Path], Path | None]:
    env_path, env_candidates = _load_runtime_env()
    config_file, config_path = _load_runtime_config_file()

    credentials_path_raw = (
        os.getenv("GOOGLE_DRIVE_CREDENTIALS_PATH")
        or config_file.get("google_drive_credentials_path")
        or "credentials.json"
    )

    root_folder_id = os.getenv("GOOGLE_DRIVE_ROOT_FOLDER_ID") or config_file.get("google_drive_root_folder_id")

    return RuntimeConfig(credentials_path_raw=credentials_path_raw, root_folder_id=root_folder_id), env_path, env_candidates, config_path


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


def ejecutar_proceso_ocr_con_resultado(fecha_objetivo: str | None = None, full_scan: bool = False) -> OCRExecutionResult:
    configurar_log()

    runtime_cfg, env_path, env_candidates, config_path = _resolve_runtime_config()
    credentials_path = _resolve_credentials_path(runtime_cfg.credentials_path_raw, env_path)
    root_folder_id = runtime_cfg.root_folder_id

    if not root_folder_id:
        env_locations = " | ".join(str(p) for p in env_candidates)
        msg = (
            "Falta GOOGLE_DRIVE_ROOT_FOLDER_ID. Puedes definirlo en .env o en app_config.json. "
            f".env encontrado: {env_path or 'NO'}. app_config.json: {config_path or 'NO'}. "
            f"Rutas .env buscadas: {env_locations}"
        )
        logging.error(msg)
        return OCRExecutionResult(dashboard_path=None, message=msg, success=False)

    if not credentials_path or not Path(credentials_path).exists():
        msg = (
            "No se encontró el archivo de credenciales de Drive. "
            f"Ruta resuelta: {credentials_path}. "
            "Configura GOOGLE_DRIVE_CREDENTIALS_PATH en .env o google_drive_credentials_path en app_config.json "
            "(si no se define, se usa credentials.json junto al .exe)."
        )
        logging.error(msg)
        return OCRExecutionResult(dashboard_path=None, message=msg, success=False)

    try:
        fecha_dashboard = resolver_fecha_objetivo(fecha_objetivo)

        drive_service = DriveImagenesService(credentials_path, root_folder_id)
        ocr_service = GeminiOCRService()
        live_service = LIVEService()
        dashboard_service = DashboardDiarioService()

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
    result = ejecutar_proceso_ocr_con_resultado("02/03/26")
    print(result.message)
