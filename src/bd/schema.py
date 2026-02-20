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
    nombre: str = Field(max_length=255)
    rut: str = Field(max_length=10, unique=True)

class Venta(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    lead_id: int = Field(sa_column=Column(Integer, ForeignKey(LEAD_ID, ondelete="RESTRICT"), nullable = False))
    detalle_venta: str = Field(max_length=255)
    monto: int
    

#Ejecutivo (Nombre / Estado / EPS)
#Lead (Datos solicitados para Front Claro)
# Venta (Lead Asociado, Detalles de la venta*)
# GeminiCache(Modelo, RequestText, RequestHash) → Extracción Data cliente Gemini-2.0-Flash-Lite / Extracción Data venta Gemini-2.5-flash-lite maybe 3-flash-preview