import os
import logging
from dotenv import load_dotenv

from src.drive.drive_imagenes import DriveImagenesService
from src.gemini.gemini_ocr_service import GeminiOCRService
from src.bd.bd_live import LIVEService
from src.config.log_config import configurar_log


def ejecutar_proceso_ocr(fecha_objetivo: str | None = None, full_scan: bool = False) -> dict:
    """Orquestador de descarga + OCR. Devuelve un resumen utilizable por JobService."""
    configurar_log()
    load_dotenv()

    credentials_path = os.getenv("GOOGLE_DRIVE_CREDENTIALS_PATH")
    root_folder_id = os.getenv("GOOGLE_DRIVE_ROOT_FOLDER_ID")

    resumen = {
        "processed": 0,
        "saved": 0,
        "warnings": [],
        "errors": [],
    }

    if not credentials_path or not root_folder_id:
        msg = "Faltan variables de entorno GOOGLE_DRIVE_CREDENTIALS_PATH / GOOGLE_DRIVE_ROOT_FOLDER_ID"
        logging.warning(msg)
        resumen["warnings"].append(msg)
        return resumen

    try:
        logging.info("Inicializando servicios de Drive y Gemini...")
        drive_service = DriveImagenesService(credentials_path, root_folder_id)
        ocr_service = GeminiOCRService()
        live_service = LIVEService()

        logging.info("Buscando imágenes para la fecha: %s", fecha_objetivo or "Ayer (default)")
        imagenes_descargadas = drive_service.obtener_imagenes(fecha_objetivo, full_scan)

        if not imagenes_descargadas:
            resumen["warnings"].append("No se encontraron imágenes para procesar")
            return resumen

        for item in imagenes_descargadas:
            ejecutivo = item["ejecutivo"]
            filename = item["filename"]
            image_bytes = item["data"]
            drive_file_id = item.get("drive_file_id")
            resumen["processed"] += 1

            try:
                resultado = ocr_service.get_respuesta_ocr(image_bytes, filename)
                saved = live_service.guardar_LIVE_metricas_sql(
                    ejecutivo_id=ejecutivo.id,
                    nombre_captura=filename,
                    metricas=resultado,
                    drive_file_id=drive_file_id,
                    content_bytes=image_bytes,
                )
                if saved:
                    resumen["saved"] += 1
            except Exception as exc:  # noqa: BLE001
                err = f"Error procesando {filename} ({ejecutivo.nombre}): {exc}"
                logging.error(err)
                resumen["errors"].append(err)

        return resumen

    except Exception as exc:  # noqa: BLE001
        err = f"Error crítico en el proceso OCR: {exc}"
        logging.error(err)
        resumen["errors"].append(err)
        return resumen


if __name__ == "__main__":
    ejecutar_proceso_ocr()
