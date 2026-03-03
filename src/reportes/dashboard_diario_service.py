from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, time
from pathlib import Path
from typing import Any
import logging

from PIL import Image, ImageDraw, ImageFont
from sqlmodel import Session, select

from src.bd.schema import Ejecutivo, LIVE
from src.config.engine_config import get_engine


@dataclass
class DashboardFila:
    fecha: date
    eps: str
    agente: str
    estado: str
    kpi_hrs_live: float
    hrs_efectivas: float
    adherencia: float | None
    leads: int | None
    ventas: int | None
    conversion: float | None
    visualizaciones: int
    espectadores_unicos: int
    espectadores_activos: int
    duracion_media_visualizacion: float | None
    peak_espectadores_simultaneos: int
    excel_subido: bool


class DashboardDiarioService:
    def __init__(self, output_dir: str = "artifacts"):
        self.engine = get_engine()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generar_dashboard_diario(self, fecha_objetivo: date) -> Path | None:
        filas = self._obtener_filas(fecha_objetivo)
        if not filas:
            logging.warning("No hay registros LIVE para construir dashboard diario")
            return None

        ruta = self.output_dir / f"dashboard_{fecha_objetivo.isoformat()}.png"
        self._render_dashboard(ruta, filas, fecha_objetivo)
        logging.info("Dashboard diario generado en %s", ruta)
        return ruta

    def _obtener_filas(self, fecha_objetivo: date) -> list[DashboardFila]:
        filas: list[DashboardFila] = []
        kpi_horas = 2.0

        with Session(self.engine) as session:
            ejecutivos = session.exec(select(Ejecutivo)).all()
            for ejecutivo in ejecutivos:
                lives = session.exec(
                    select(LIVE).where(
                        LIVE.ejecutivo_id == ejecutivo.id,
                        LIVE.fecha_live == fecha_objetivo,
                    )
                ).all()
                if not lives:
                    continue

                horas_efectivas = round(
                    sum(self._time_to_hours(live.duracion_live) for live in lives), 2
                )
                adherencia = None
                if horas_efectivas > 0:
                    adherencia = round(kpi_horas / horas_efectivas, 2)

                duraciones_media = [
                    self._time_to_seconds(live.duracion_media_visualizacion)
                    for live in lives
                    if live.duracion_media_visualizacion
                ]
                duracion_media_seg = (
                    sum(duraciones_media) / len(duraciones_media)
                    if duraciones_media
                    else None
                )

                filas.append(
                    DashboardFila(
                        fecha=fecha_objetivo,
                        eps=ejecutivo.eps,
                        agente=ejecutivo.nombre,
                        estado=ejecutivo.estado,
                        kpi_hrs_live=kpi_horas,
                        hrs_efectivas=horas_efectivas,
                        adherencia=adherencia,
                        leads=None,
                        ventas=None,
                        conversion=None,
                        visualizaciones=sum((live.visualizaciones or 0) for live in lives),
                        espectadores_unicos=sum((live.espectadores_unicos or 0) for live in lives),
                        espectadores_activos=sum((live.espectadores_activos or 0) for live in lives),
                        duracion_media_visualizacion=(
                            round(duracion_media_seg / 60, 2)
                            if duracion_media_seg is not None
                            else None
                        ),
                        peak_espectadores_simultaneos=max(
                            (live.pico_espectadores_simultaneos or 0) for live in lives
                        ),
                        excel_subido=False,
                    )
                )

        return filas

    @staticmethod
    def _time_to_seconds(value: time | None) -> int:
        if not value:
            return 0
        return value.hour * 3600 + value.minute * 60 + value.second

    @classmethod
    def _time_to_hours(cls, value: time | None) -> float:
        return round(cls._time_to_seconds(value) / 3600, 2)

    def _render_dashboard(
        self, path: Path, filas: list[DashboardFila], fecha_objetivo: date
    ) -> None:
        width = 1800
        header_h = 130
        row_h = 46
        footer_h = 80
        height = header_h + (len(filas) + 2) * row_h + footer_h

        image = Image.new("RGB", (width, height), (245, 248, 252))
        draw = ImageDraw.Draw(image)
        title_font = ImageFont.load_default()
        body_font = ImageFont.load_default()

        draw.rectangle([(0, 0), (width, 100)], fill=(21, 71, 132))
        draw.text((20, 35), f"Dashboard Control Diario - {fecha_objetivo}", fill="white", font=title_font)

        columns = [
            "FECHA", "EPS", "AGENTE", "ESTADO", "KPI HRS LIVE", "HRS EFECTIVAS",
            "% ADHERENCIA", "LEADS", "VENTAS", "% CONVERSION", "VISUALIZACIONES",
            "ESPECTADORES UNICOS", "ESPECTADORES ACTIVOS", "DURACION MEDIA (MIN)",
            "PEAK ESPECTADORES SIMULTANEOS", "EXCEL"
        ]

        col_widths = [120, 80, 130, 90, 110, 110, 110, 70, 70, 100, 110, 140, 140, 140, 180, 80]

        x = 10
        y = 110
        for col, col_w in zip(columns, col_widths):
            draw.rectangle([(x, y), (x + col_w, y + row_h)], fill=(220, 230, 242), outline=(180, 190, 210))
            draw.text((x + 4, y + 14), col, fill=(20, 30, 50), font=body_font)
            x += col_w

        for i, fila in enumerate(filas, start=1):
            x = 10
            y_row = y + i * row_h
            valores = [
                str(fila.fecha), fila.eps, fila.agente, fila.estado,
                f"{fila.kpi_hrs_live:.2f}", f"{fila.hrs_efectivas:.2f}",
                self._fmt_nullable(fila.adherencia),
                self._fmt_nullable(fila.leads),
                self._fmt_nullable(fila.ventas),
                self._fmt_nullable(fila.conversion),
                str(fila.visualizaciones), str(fila.espectadores_unicos),
                str(fila.espectadores_activos),
                self._fmt_nullable(fila.duracion_media_visualizacion),
                str(fila.peak_espectadores_simultaneos),
                "SI" if fila.excel_subido else "NO",
            ]
            row_color = (255, 255, 255) if i % 2 else (248, 250, 253)
            for valor, col_w in zip(valores, col_widths):
                draw.rectangle([(x, y_row), (x + col_w, y_row + row_h)], fill=row_color, outline=(220, 225, 235))
                draw.text((x + 4, y_row + 14), valor, fill=(40, 50, 70), font=body_font)
                x += col_w

        warning_y = y + (len(filas) + 1) * row_h + 18
        warning_text = "Aviso: LEADS / VENTAS en NULL porque el ejecutivo aun no ha subido su Excel al Drive."
        draw.text((20, warning_y), warning_text, fill=(170, 60, 40), font=body_font)

        # Gráfico simple de barras de visualizaciones por agente
        chart_top = warning_y + 28
        chart_left = 20
        chart_height = 120
        chart_width = width - 60
        draw.rectangle(
            [(chart_left, chart_top), (chart_left + chart_width, chart_top + chart_height)],
            outline=(180, 190, 210),
            fill=(252, 253, 255),
        )

        max_vis = max((fila.visualizaciones for fila in filas), default=1)
        bar_space = chart_width // max(len(filas), 1)
        for idx, fila in enumerate(filas):
            bar_x1 = chart_left + idx * bar_space + 15
            bar_x2 = bar_x1 + max(bar_space - 30, 20)
            bar_h = int((fila.visualizaciones / max_vis) * (chart_height - 35)) if max_vis else 0
            bar_y1 = chart_top + chart_height - 20 - bar_h
            bar_y2 = chart_top + chart_height - 20
            draw.rectangle([(bar_x1, bar_y1), (bar_x2, bar_y2)], fill=(51, 123, 196))
            draw.text((bar_x1, bar_y2 + 2), fila.agente[:12], fill=(40, 50, 70), font=body_font)

        image.save(path)

    @staticmethod
    def _fmt_nullable(value: Any) -> str:
        if value is None:
            return "NULL"
        if isinstance(value, float):
            return f"{value:.2f}"
        return str(value)


def resolver_fecha_objetivo(fecha_objetivo: str | None) -> date:
    if fecha_objetivo:
        return datetime.strptime(fecha_objetivo, "%d/%m/%y").date()
    return (datetime.now() - timedelta(days=1)).date()
