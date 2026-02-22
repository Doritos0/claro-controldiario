from functools import lru_cache
from os import environ

class LlmConfig:
    gemini_api_key: str
    gemini_model_ocr: str

    def __init__(self, gemini_api_key: str, gemini_model_ocr: str):
        self.gemini_api_key = gemini_api_key
        self.gemini_model_ocr = gemini_model_ocr

@lru_cache(maxsize=1)
def get_llm_config() -> LlmConfig:
    gemini_api_key = environ.get("GEMINI_API_KEY")
    assert gemini_api_key, "La variable de entorno GEMINI_API_KEY no está configurada"

    gemini_model_ocr = environ.get("GEMINI_MODEL_OCR")
    assert gemini_model_ocr, "La variable de entorno GEMINI_MODEL_OCR no está configurada"

    config = LlmConfig(
        gemini_api_key=gemini_api_key,
        gemini_model_ocr=gemini_model_ocr
    )

    return config