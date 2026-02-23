from pydantic import BaseModel
from datetime import date, time

class LIVERespuesta(BaseModel):
    fecha_live: date | None
    hora_inicio_live: str | None
    duracion_live: str | None
    hora_termino_live: str | None
    visualizaciones: int | None
    espectadores_unicos: int | None
    espectadores_activos: int | None
    duracion_media_visualizacion: time | None
    pico_espectadores_simultaneos: int | None