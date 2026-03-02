from datetime import date, datetime, time

from sqlalchemy import Column, ForeignKey, Integer, UniqueConstraint
from sqlmodel import Field, SQLModel

EJECUTIVO_ID = "ejecutivo.id"
LEAD_ID = "lead.id"


class Ejecutivo(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    nombre: str
    estado: str
    eps: str


class Lead(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    ejecutivo_id: int = Field(sa_column=Column(Integer, ForeignKey(EJECUTIVO_ID, ondelete="RESTRICT"), nullable=False))
    nombre: str | None = Field(max_length=255)
    rut: str = Field(max_length=10)


class Venta(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    lead_id: int = Field(sa_column=Column(Integer, ForeignKey(LEAD_ID, ondelete="RESTRICT"), nullable=False))
    fecha_venta: date = Field()


class LIVE(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    ejecutivo_id: int = Field(sa_column=Column(Integer, ForeignKey(EJECUTIVO_ID, ondelete="RESTRICT"), nullable=False))
    fecha_live: date | None = Field(default=None, nullable=True)
    hora_inicio: time | None = Field(default=None, nullable=True)
    duracion_live: time | None = Field(default=None, nullable=True)
    hora_termino: time | None = Field(default=None, nullable=True)
    visualizaciones: int | None = Field(default=None, nullable=True)
    espectadores_unicos: int | None = Field(default=None, nullable=True)
    espectadores_activos: int | None = Field(default=None, nullable=True)
    duracion_media_visualizacion: time | None = Field(default=None, nullable=True)
    pico_espectadores_simultaneos: int | None = Field(default=None, nullable=True)
    nombre_captura: str = Field()
    drive_file_id: str | None = Field(default=None, index=True)
    content_hash: str | None = Field(default=None, index=True)


class RequestCache(SQLModel, table=True):
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


class ExecutiveDailySummary(SQLModel, table=True):
    __tablename__ = "executive_daily_summary"
    __table_args__ = (UniqueConstraint("ejecutivo_id", "fecha", name="uq_exec_summary_fecha"),)

    id: int | None = Field(default=None, primary_key=True)
    ejecutivo_id: int = Field(sa_column=Column(Integer, ForeignKey(EJECUTIVO_ID, ondelete="RESTRICT"), nullable=False))
    fecha: date
    leads: int | None = Field(default=None, nullable=True)
    ventas: int | None = Field(default=None, nullable=True)
    total_rows: int | None = Field(default=None, nullable=True)
    warnings: str | None = Field(default=None, nullable=True)
    excel_drive_file_id: str | None = Field(default=None, nullable=True, index=True)


class JobRun(SQLModel, table=True):
    __tablename__ = "job_run"

    id: int | None = Field(default=None, primary_key=True)
    status: str = Field(default="PENDING", index=True)
    fecha_objetivo: str
    fecha_siguiente: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    warnings_json: str = Field(default="[]")


class JobLog(SQLModel, table=True):
    __tablename__ = "job_log"

    id: int | None = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="job_run.id", index=True)
    stage: str = Field(index=True)
    level: str = Field(default="INFO")
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
