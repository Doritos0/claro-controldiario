from __future__ import annotations

from datetime import datetime
from pathlib import Path

from src.bd.bd_ejecutivo import EjecutivoService
from src.bd.bd_live import LIVEService
from src.bd.schema import Ejecutivo
from src.gemini.gemini_ocr_service import GeminiOCRService


class LocalImageService:
    def __init__(self, base_path: Path | None = None):
        self.base_path = base_path or (Path(__file__).resolve().parents[2] / 'whatsapp-service' / 'src' / 'descargas')
        self.ejecutivo_service = EjecutivoService()
        self.live_service = LIVEService()
        self.ocr_service = GeminiOCRService()

    def procesar_carpeta_fecha(self, fecha: str, empresa_id: int) -> int:
        nombre_carpeta = fecha.replace('/', '-')
        carpeta = self.base_path / nombre_carpeta
        if not carpeta.exists():
            raise FileNotFoundError(f'No existe carpeta para fecha {fecha}: {carpeta}')

        ejecutivos = self.ejecutivo_service.get_ejecutivos_sql(empresa_id=empresa_id)
        if not ejecutivos:
            raise ValueError('No hay ejecutivos registrados para la empresa.')

        ejecutivo_destino: Ejecutivo = ejecutivos[0]
        procesadas = 0
        for archivo in carpeta.iterdir():
            if archivo.suffix.lower() not in {'.jpg', '.jpeg', '.png', '.webp'}:
                continue
            resultado = self.ocr_service.get_respuesta_ocr(archivo.read_bytes(), archivo.name)
            self.live_service.guardar_LIVE_metricas_sql(ejecutivo_destino.id, archivo.name, resultado)
            procesadas += 1

        return procesadas

    @staticmethod
    def normalizar_fecha_iso(fecha_iso: str) -> str:
        fecha = datetime.strptime(fecha_iso, '%Y-%m-%d')
        return fecha.strftime('%d/%m/%y')
