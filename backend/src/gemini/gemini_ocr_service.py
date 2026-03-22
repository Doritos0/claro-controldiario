from datetime import datetime
import logging
import time
from io import BytesIO
from PIL import Image
from google.genai import types

from src.gemini.estructura import LIVERespuesta
from src.gemini.gemini_base_service import GeminiBaseService, ImagenInfo
from src.bd.bd_live import LIVEService


class GeminiOCRService(GeminiBaseService):
    def __init__(self):
        super().__init__()
        self.live_service = LIVEService()

    def get_respuesta_ocr(self, image_bytes: bytes, filename: str) -> LIVERespuesta:
        """
        Recibe los bytes de una imagen descargada de Drive,
        la procesa con Gemini y guarda en caché.
        """

        respuesta = self.live_service.get_LIVE_por_captura(nombre_captura=filename)

        if respuesta:
            logging.debug("LIVE ya procesado")
            return respuesta

        try:
            # 1. Obtener metadatos de la imagen con PIL
            with Image.open(BytesIO(image_bytes)) as img:
                width, height = img.size
                # Convertimos a formato compatible si es necesario (ej: TIFF a PNG)
                format_detected = img.format.lower()
                mime_type = f"image/{format_detected}"

                user_prompt_str = (
                    "Eres un experto en extracción de datos. Extrae las métricas de TikTok LIVE de la imagen en formato JSON. "
                    f"Asume que el año actual es {datetime.now().year}. "
                    "REGLAS CRÍTICAS DE FORMATO: "
                    "1. fecha_live: Formato 'YYYY-MM-DD'. "
                    "2. Tiempos (inicio, duración, término, media): Formato 'HH:MM:SS'. "
                    "   - Si la duración es '47 min', escribe '00:47:00'. "
                    "   - Si es '1 h 3 min', escribe '01:03:00'. "
                    "   - PROHIBIDO: No añadas zonas horarias, ni sufijos como '-26:00', '+00:00' o la letra 'Z'. "
                    "   - PROHIBIDO: No incluyas microsegundos. "
                    "   - hora_termino_live debe ser la suma de hora_inicio_live + duracion_live, en caso no encontrar alguna de estas hora_termino_live sera null "
                    "3. Números: Solo enteros sin puntos ni comas. "
                    "4. Si un dato no es visible o no se encuentra, usa null. "
                    "EJEMPLO DE SALIDA: "
                    "{"
                    '"fecha_live": "2026-02-06", "hora_inicio_live": "15:16:00", "duracion_live": "00:47:00", '
                    '"hora_termino_live": "16:03:00", "visualizaciones": 2600, "espectadores_unicos": 2200, '
                    '"espectadores_activos": 101, "duracion_media_visualizacion": "00:00:37", "pico_espectadores_simultaneos": 261'
                    "}"
                    ""
                )

            # 3. Verificar Caché (usando el método de tu GeminiBaseService)
            request_hash = self.hash_contenido(user_prompt_str, image_bytes)
            cached = self.obtener_request_ocr_hash(request_hash)
            if cached:
                logging.info(f"Imagen {filename} encontrada en caché.")
                return LIVERespuesta.model_validate_json(cached.response_text)

            # 4. Preparar solicitud para Gemini
            imagen_info = ImagenInfo(
                data=image_bytes, mime_type=mime_type, width=width, height=height
            )

            user_content = types.Part.from_text(text=user_prompt_str)
            byte_content = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

            # 5. Llamada a la API
            start_time = time.time()
            response, live_respuesta = self.obtener_respuesta_ocr(
                [user_content, byte_content]
            )
            tiempo_ms = int((time.time() - start_time) * 1000)

            response_text = live_respuesta.model_dump_json(indent=2)

            # 6. Guardar en SQLModel (RequestCache)
            token_info = self.get_tokens(imagen_info, response)
            request_description = f"Drive Image: {filename} ({mime_type})"

            self.guardar_request_ocr_hash(
                request_text=request_description,
                request_hash=request_hash,
                response_text=response_text,
                token_info=token_info,
                tiempo_ms=tiempo_ms,
            )

            return live_respuesta

        except Exception as e:
            logging.error(f"Error procesando imagen de Drive {filename}: {e}")
            raise
