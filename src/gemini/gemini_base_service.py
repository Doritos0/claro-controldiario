import hashlib
import logging
from pydantic import BaseModel

from google.genai import Client
from google.genai.types import GenerateContentConfig, GenerateContentResponse,Part

from src.bd.bd_request_cache import RequestCacheService, TokenInfo
from src.config.llm_config import LlmConfig, get_llm_config

from src.gemini.estructura import LIVERespuesta

class ImagenInfo(BaseModel):
    data: bytes
    mime_type: str
    width: int
    height: int

class GeminiBaseService:
    def __init__(self):
        llm_config: LlmConfig = get_llm_config()
        self.client: Client = Client(api_key=llm_config.gemini_api_key)
        self.model_ocr = llm_config.gemini_model_ocr
        if self.model_ocr.startswith("gemini-2.5"):
            self.model_ocr_config = GenerateContentConfig(response_mime_type="application/json", response_schema=LIVERespuesta)
        else:
            raise ValueError(f"Modelo OCR no soportado: {self.model_ocr}")
        self.request_cache_service = RequestCacheService()

    def obtener_respuesta_ocr(self, contents: list[Part]) -> tuple[GenerateContentResponse, LIVERespuesta]:
        response = self.client.models.generate_content(model=self.model_ocr, contents=contents, config=self.model_ocr_config)
        ocr_respuesta : LIVERespuesta = LIVERespuesta.model_validate_json(response.text)

        return response, ocr_respuesta
    
    def obtener_request_ocr_hash(self, request_hash: str):
        response = self.request_cache_service.obtener_request_cache_sql(self.model_ocr, request_hash)
    
    def guardar_request_ocr_hash(self, request_text: str, request_hash: str, response_text: str, token_info: TokenInfo, tiempo_ms: int) -> None:
        self.request_cache_service.guardar_request_cache_sql(self.model_ocr, request_text, request_hash, response_text, token_info, tiempo_ms)

    @staticmethod
    def hash_contenido(prompt: str, data: bytes) -> str:
        h = hashlib.sha256()
        h.update(prompt.encode("utf-8"))
        h.update(data)
        return h.hexdigest()
    
    @staticmethod
    def get_tokens(imagen_info: ImagenInfo, response: GenerateContentResponse) -> TokenInfo | None:
        try:
            usage = response.usage_metadata
            token_info = TokenInfo(
                size=(len(imagen_info.data)),
                width=imagen_info.width,
                height=imagen_info.height,
                input_tokens=usage.prompt_token_count or 0,
                thoughts_tokens=usage.thoughts_token_count or 0,
                output_tokens=usage.candidates_token_count or 0,
                total_tokens=usage.total_token_count or 0,
            )
            return token_info
        except Exception as e:
            logging.info(f"No se pudieron registrar los tokens: {e}")
            return None
        
    @staticmethod
    def get_tokens_texto(response: GenerateContentResponse) -> TokenInfo | None:
        try:
            usage = response.usage_metadata
            token_info = TokenInfo(
                size=0,
                width=0,
                height=0,
                input_tokens=usage.prompt_token_count or 0,
                thoughts_tokens=usage.thoughts_token_count or 0,
                output_tokens=usage.candidates_token_count or 0,
                total_tokens=usage.total_token_count or 0,
            )
            return token_info
        except Exception as e:
            logging.info(f"No se pudieron registrar los tokens: {e}")
            return None