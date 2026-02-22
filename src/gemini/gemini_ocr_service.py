import logging
import time
from io import BytesIO
from PIL import Image
from google.genai import types

from src.gemini.gemini_base_service import GeminiBaseService, ImagenInfo

class GeminiOCRService(GeminiBaseService):
    def __init__(self):
        super().__init__()

    def procesar_imagen_drive(self, image_bytes: bytes, filename: str) -> str:
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
                "Extrae las siguientes métricas de la imagen: "
                "Agente (título), Horas Efectivas (duración total), Visualizaciones, "
                "Espectadores Unicos, Espectadores Activos, Duración media de visualización, "
                "Peak Espectadores (pico simultáneo) y Adherencia (media simultánea). "
                "Devuelve solo los datos, sin texto adicional."
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
            response = self.obtener_respuesta_ocr([user_content, byte_content])
            tiempo_ms = int((time.time() - start_time) * 1000)
            
            response_text = response.text or ""

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

            return response_text

        except Exception as e:
            logging.error(f"Error procesando imagen de Drive {filename}: {e}")
            raise