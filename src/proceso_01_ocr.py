import os
import logging
from dotenv import load_dotenv

# Importamos tus servicios
from src.bd.schema import Ejecutivo
from src.drive.drive_imagenes import DriveImagenesService
from src.gemini.gemini_ocr_service import GeminiOCRService
from src.bd.bd_live import LIVEService


# Configuración de logging para ver qué está pasando en consola
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def ejecutar_proceso_ocr(fecha_objetivo: str = None):
    """
    Orquestador que descarga imágenes de Drive y las procesa con Gemini OCR.
    """
    # 1. Cargar configuración desde el .env
    load_dotenv()
    
    credentials_path = os.getenv("GOOGLE_DRIVE_CREDENTIALS_PATH")
    root_folder_id = os.getenv("GOOGLE_DRIVE_ROOT_FOLDER_ID")

    if not credentials_path or not root_folder_id:
        logging.error("Faltan variables de entorno en el archivo .env")
        return

    try:
        # 2. Inicializar servicios
        logging.info("Inicializando servicios de Drive y Gemini...")
        drive_service = DriveImagenesService(credentials_path, root_folder_id)
        ocr_service = GeminiOCRService()
        live_service = LIVEService()

        # 3. Obtener imágenes del día
        # Si fecha_objetivo es None, el servicio tomará el día de ayer por defecto
        logging.info(f"Buscando imágenes para la fecha: {fecha_objetivo or 'Ayer (default)'}")
        imagenes_descargadas = drive_service.obtener_imagenes_del_dia(fecha_objetivo)

        if not imagenes_descargadas:
            logging.warning("No se encontraron imágenes para procesar.")
            return

        logging.info(f"Se encontraron {len(imagenes_descargadas)} imágenes. Iniciando OCR...")

        # 4. Procesar cada imagen
        for item in imagenes_descargadas:
            ejecutivo: Ejecutivo = item['ejecutivo']
            filename = item['filename']
            image_bytes = item['data']

            logging.info(f"--- Procesando: {filename} (Ejecutivo: {ejecutivo}) ---")

            # Llamada al servicio OCR
            resultado = ocr_service.get_respuesta_ocr(image_bytes, filename)

            live_service.guardar_LIVE_metricas_sql(ejecutivo.id, resultado)

            # 5. Mostrar resultado por consola
            print(f"\nRESULTADO PARA {ejecutivo} ({filename}):")
            print("-" * 40)
            print(resultado)
            print("-" * 40 + "\n")

    except Exception as e:
        logging.error(f"Error crítico en el proceso: {e}")

if __name__ == "__main__":
    # Puedes pasar una fecha específica como "18/02/26" o dejarlo vacío para "ayer"
    # Ejemplo: ejecutar_proceso_ocr("18/02/26")
    #ejecutar_proceso_ocr()
    ejecutar_proceso_ocr("18/02/26")