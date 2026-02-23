from pydantic import BaseModel
from datetime import date, time

class LIVERespuesta(BaseModel):
    fecha_live: date
    hora_inicio_live: time
    duracion_live: time
    hora_termino_live: time
    visualizaciones: int
    espectadores_unicos: int
    espectadores_activos: int
    duracion_media_visualizacion: time
    pico_espectadores_simultaneos: int