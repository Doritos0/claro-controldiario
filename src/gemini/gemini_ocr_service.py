import logging
import time
from io import BytesIO
from PIL import Image
from google.genai import types

from src.gemini.estructura import LIVERespuesta
from src.gemini.gemini_base_service import GeminiBaseService, ImagenInfo

class GeminiOCRService(GeminiBaseService):
    def __init__(self):
        super().__init__()

    def get_respuesta_ocr(self, image_bytes: bytes, filename: str) -> LIVERespuesta:
        """
        Recibe los bytes de una imagen descargada de Drive,
        la procesa con Gemini y guarda en caché.
        """
        try:
            # 1. Obtener metadatos de la imagen con PIL
            with Image.open(BytesIO(image_bytes)) as img:
                width, height = img.size
                # Convertimos a formato compatible si es necesario (ej: TIFF a PNG)
                format_detected = img.format.lower()
                mime_type = f"image/{format_detected}"
                
            user_prompt_str = (
                "Eres un asistente experto en lectura de imagenes y conversion a texto. "
                "Recibiras una imagen obtenida desde un archivo PNG que consisten en metricas claves de un TikTok LIVE"
                "Debes devolver Fecha LIVE, Hora Inicio LIVE, Duracion LIVE, Hora Termino LIVE (Hora Inicio + Duracion LIVE)"
                "Visualizaciones, Espectadores Unicos, Espectadores Activos, Duracion media de la visualizacion, Pico de espectadores simultaneos"
                "Por favor, organiza esta información en una estructura con las columnas correspondientes a los datos solicitados"
                "En caso de no encontrar nada, devolver columnas vacias"
            )
            
            # 3. Verificar Caché (usando el método de tu GeminiBaseService)
            request_hash = self.hash_contenido(user_prompt_str, image_bytes)
            cached = self.obtener_request_ocr_hash(request_hash)
            if cached:
                logging.info(f"Imagen {filename} encontrada en caché.")
                return cached.response_text

            # 4. Preparar solicitud para Gemini
            imagen_info = ImagenInfo(
                data=image_bytes, 
                mime_type=mime_type, 
                width=width, 
                height=height
            )
            
            user_content = types.Part.from_text(text=user_prompt_str)
            byte_content = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
            
            # 5. Llamada a la API
            start_time = time.time()
            response, live_respuesta = self.obtener_respuesta_ocr([user_content, byte_content])
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
                tiempo_ms=tiempo_ms
            )

            return live_respuesta

        except Exception as e:
            logging.error(f"Error procesando imagen de Drive {filename}: {e}")
            raise