from datetime import datetime, date, time
from sqlmodel import Field, SQLModel
from sqlalchemy import Column, ForeignKey, Index, Integer


EJECUTIVO_ID = "ejecutivo.id"
LEAD_ID = "lead.id"

class Ejecutivo(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    nombre: str
    estado: str #EnumEstado
    eps: str

class Lead(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    ejecutivo_id: int = Field(sa_column=Column(Integer, ForeignKey(EJECUTIVO_ID, ondelete="RESTRICT"), nullable = False))
    nombre: str | None = Field(max_length=255)
    rut: str = Field(max_length=10)

class Venta(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    lead_id: int = Field(sa_column=Column(Integer, ForeignKey(LEAD_ID, ondelete="RESTRICT"), nullable = False))
    fecha_venta: date = Field()

class LIVE(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    ejecutivo_id: int = Field(sa_column=Column(Integer, ForeignKey(EJECUTIVO_ID, ondelete="RESTRICT"), nullable = False))
    fecha_live: date = Field(default=None, nullable=True)
    hora_inicio: time = Field(default=None, nullable=True)
    duracion_live: time = Field(default=None, nullable=True)
    hora_termino: time = Field(default=None, nullable=True)
    visualizaciones: int = Field(default=None, nullable=True)
    espectadores_unicos: int = Field(default=None, nullable=True)
    espectadores_activos: int = Field(default=None, nullable=True)
    duracion_media_visualizacion: time = Field(default=None, nullable=True)
    pico_espectadores_simultaneos: int = Field(default=None, nullable=True)
    nombre_captura: str = Field()

class RequestCache(SQLModel, table=True):  # pyright: ignore[reportCallIssue]
    id: int | None = Field(default=None, primary_key=True)
    model: str = Field(max_length=50)
    fecha: datetime = Field()
    request_text: str = Field(default="")
    request_hash: str = Field(max_length=64)
    response_text: str = Field()
    tiempo_ms: int = Field()
    imagen_size: int = Field(default=0)
    imagen_x: int = Field(default=0)
    imagen_y: int = Field(default=0)
    tokens_input: int = Field(default=0)
    tokens_thoughts: int = Field(default=0)
    tokens_output: int = Field(default=0)
    tokens_total: int = Field(default=0)
    

#Ejecutivo (Nombre / Estado / EPS)
#Lead (Datos solicitados para Front Claro)
# Venta (Lead Asociado, Detalles de la venta*)
# GeminiCache(Modelo, RequestText, RequestHash) → Extracción Data cliente Gemini-2.0-Flash-Lite / Extracción Data venta Gemini-2.5-flash-lite maybe 3-flash-preview