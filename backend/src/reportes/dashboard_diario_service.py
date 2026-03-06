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

TRAMOS = [
    ("11-14", 11, 14),
    ("14-17", 14, 17),
    ("17-20", 17, 20),
]


def load_fonts() -> dict[str, ImageFont.FreeTypeFont]:
    """
    Carga fuentes TrueType para que el dashboard sea legible (Windows).
    Usa Segoe UI como default; cae a la fuente por defecto si no están disponibles.
    """
    regular_path = r"C:\Windows\Fonts\segoeui.ttf"
    bold_path = r"C:\Windows\Fonts\segoeuib.ttf"

    try:
        return {
            "title": ImageFont.truetype(bold_path, 34),
            "subtitle": ImageFont.truetype(regular_path, 18),

            "section": ImageFont.truetype(bold_path, 20),

            "card_label": ImageFont.truetype(regular_path, 16),
            "card_value": ImageFont.truetype(bold_path, 22),

            "table_header": ImageFont.truetype(bold_path, 14),
            "table_cell": ImageFont.truetype(regular_path, 13),

            "small": ImageFont.truetype(regular_path, 12),
        }
    except Exception:
        # Fallback (menos legible, pero evita crash)
        default = ImageFont.load_default()
        return {
            "title": default,
            "subtitle": default,
            "section": default,
            "card_label": default,
            "card_value": default,
            "table_header": default,
            "table_cell": default,
            "small": default,
        }


def draw_text_upper(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, font, fill):
    draw.text(xy, (text or "").upper(), font=font, fill=fill)


@dataclass
class DashboardFila:
    fecha: date
    eps: str
    agente: str
    estado: str
    kpi_hrs_live: float
    hrs_efectivas_seg: int
    adherencia: float | None
    leads: int | None
    ventas: int | None
    conversion: float | None
    visualizaciones_totales: int
    visualizaciones_promedio: float
    espectadores_unicos: int
    espectadores_activos: int
    duracion_media_visualizacion_seg: int | None
    peak_espectadores_simultaneos: int
    factor: float | None
    excel_subido: bool
    lives_por_tramo: dict[str, int]
    vis_promedio_por_tramo: dict[str, float]


class DashboardDiarioService:
    def __init__(self, output_dir: str = "artifacts"):
        self.engine = get_engine()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generar_dashboard_diario(self, fecha_objetivo: date, empresa_id: int | None = None) -> Path | None:
        filas = self._obtener_filas(fecha_objetivo, empresa_id=empresa_id)
        if not filas:
            logging.warning("No hay registros LIVE para construir dashboard diario")
            return None

        ruta = self.output_dir / f"dashboard_{fecha_objetivo.isoformat()}.png"
        self._render_dashboard(ruta, filas, fecha_objetivo)
        logging.info("Dashboard diario generado en %s", ruta)
        return ruta

    def _obtener_filas(self, fecha_objetivo: date, empresa_id: int | None = None) -> list[DashboardFila]:
        filas: list[DashboardFila] = []
        kpi_horas = 2.0

        with Session(self.engine) as session:
            statement = select(Ejecutivo)
            if empresa_id is not None:
                statement = statement.where(Ejecutivo.empresa_id == empresa_id)
            ejecutivos = session.exec(statement).all()
            for ejecutivo in ejecutivos:
                lives = session.exec(
                    select(LIVE).where(
                        LIVE.ejecutivo_id == ejecutivo.id,
                        LIVE.fecha_live == fecha_objetivo,
                    )
                ).all()
                if not lives:
                    continue

                horas_efectivas_seg = sum(self._time_to_seconds(live.duracion_live) for live in lives)
                horas_efectivas = horas_efectivas_seg / 3600
                adherencia = round(horas_efectivas / kpi_horas, 2) if horas_efectivas > 0 else None

                duraciones_media = [
                    self._time_to_seconds(live.duracion_media_visualizacion)
                    for live in lives
                    if live.duracion_media_visualizacion
                ]
                duracion_media_seg = int(sum(duraciones_media) / len(duraciones_media)) if duraciones_media else None

                visualizaciones = [(live.visualizaciones or 0) for live in lives]
                visualizaciones_totales = sum(visualizaciones)
                visualizaciones_promedio = round(visualizaciones_totales / len(lives), 2) if lives else 0.0
                peak_maximo = max((live.pico_espectadores_simultaneos or 0) for live in lives)
                factor = round(visualizaciones_promedio / peak_maximo, 2) if peak_maximo > 0 else None

                lives_por_tramo = {tramo: 0 for tramo, _, _ in TRAMOS}
                visualizaciones_por_tramo: dict[str, list[int]] = {tramo: [] for tramo, _, _ in TRAMOS}

                for live in lives:
                    tramo = self._resolver_tramo(live.hora_inicio)
                    if not tramo:
                        continue
                    lives_por_tramo[tramo] += 1
                    visualizaciones_por_tramo[tramo].append(live.visualizaciones or 0)

                vis_promedio_por_tramo = {
                    tramo: round(sum(valores) / len(valores), 2) if valores else 0.0
                    for tramo, valores in visualizaciones_por_tramo.items()
                }

                filas.append(
                    DashboardFila(
                        fecha=fecha_objetivo,
                        eps=ejecutivo.eps,
                        agente=ejecutivo.nombre,
                        estado=ejecutivo.estado,
                        kpi_hrs_live=kpi_horas,
                        hrs_efectivas_seg=horas_efectivas_seg,
                        adherencia=adherencia,
                        leads=None,
                        ventas=None,
                        conversion=None,
                        visualizaciones_totales=visualizaciones_totales,
                        visualizaciones_promedio=visualizaciones_promedio,
                        espectadores_unicos=sum((live.espectadores_unicos or 0) for live in lives),
                        espectadores_activos=sum((live.espectadores_activos or 0) for live in lives),
                        duracion_media_visualizacion_seg=duracion_media_seg,
                        peak_espectadores_simultaneos=peak_maximo,
                        factor=factor,
                        excel_subido=False,
                        lives_por_tramo=lives_por_tramo,
                        vis_promedio_por_tramo=vis_promedio_por_tramo,
                    )
                )

        return sorted(filas, key=lambda x: x.visualizaciones_totales, reverse=True)

    @staticmethod
    def _resolver_tramo(value: time | None) -> str | None:
        if value is None:
            return None
        for tramo, inicio, fin in TRAMOS:
            if inicio <= value.hour < fin:
                return tramo
        return None

    @staticmethod
    def _time_to_seconds(value: time | None) -> int:
        if not value:
            return 0
        return value.hour * 3600 + value.minute * 60 + value.second

    @staticmethod
    def _seconds_to_hhmmss(seconds: int | None) -> str:
        if seconds is None:
            return "NULL"
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"

    def _render_dashboard(self, path: Path, filas: list[DashboardFila], fecha_objetivo: date) -> None:
        width = 2200
        height = 1850  # un poco más alto para soportar fuentes grandes
        image = Image.new("RGB", (width, height), (252, 245, 246))
        draw = ImageDraw.Draw(image)

        fonts = load_fonts()

        color_primary = (200, 16, 46)
        color_primary_dark = (140, 10, 30)
        color_card = (255, 255, 255)
        color_text = (45, 26, 30)
        color_muted = (108, 78, 84)
        color_border = (231, 210, 214)
        color_bg = (252, 245, 246)

        # HEADER (más alto y con texto grande)
        draw.rectangle([(0, 0), (width, 140)], fill=color_primary)
        draw_text_upper(draw, (24, 18), "CLARO | CONTROL DIARIO", font=fonts["title"], fill="white")
        draw_text_upper(
            draw,
            (24, 60),
            f"FECHA: {fecha_objetivo.strftime('%Y-%m-%d')}  |  ENFOQUE: DESEMPEÑO POR EJECUTIVO",
            font=fonts["subtitle"],
            fill="white",
        )

        # KPI cards
        total_lives = sum(sum(f.lives_por_tramo.values()) for f in filas)
        total_visualizaciones = sum(f.visualizaciones_totales for f in filas)
        prom_factor = self._avg([f.factor for f in filas if f.factor is not None])
        mejor_ejecutivo_vis = max(filas, key=lambda f: f.visualizaciones_totales)

        cards = [
            ("Ejecutivos con live", str(len(filas))),
            ("Total lives del dia", str(total_lives)),
            ("Visualizaciones totales", f"{total_visualizaciones}"),
            ("Factor promedio", self._fmt_nullable(prom_factor)),
            ("Top visualizaciones", f"{mejor_ejecutivo_vis.agente} ({mejor_ejecutivo_vis.visualizaciones_totales})"),
        ]

        card_y, card_h, card_w, card_gap = 160, 100, 410, 15
        x = 24
        for titulo, valor in cards:
            draw.rounded_rectangle(
                [(x, card_y), (x + card_w, card_y + card_h)],
                radius=14,
                fill=color_card,
                outline=color_border,
            )
            draw_text_upper(draw, (x + 12, card_y + 12), titulo, fill=color_muted, font=fonts["card_label"])
            draw.text((x + 12, card_y + 50), str(valor), fill=color_primary_dark, font=fonts["card_value"])
            x += card_w + card_gap

        # Tabla principal por ejecutivo
        y = 290
        draw_text_upper(draw, (24, y - 32), "Resumen principal por ejecutivo", fill=color_primary_dark, font=fonts["section"])

        columns = [
            "AGENTE", "EPS", "ESTADO", "KPI", "HRS EFECTIVAS", "ADHERENCIA",
            "VIS TOTAL", "VIS PROM", "ESP UNICOS", "ESP ACTIVOS", "DUR. MEDIA", "PEAK", "FACTOR", "EXCEL"
        ]
        col_widths = [180, 100, 100, 65, 130, 105, 100, 100, 110, 110, 110, 90, 90, 70]

        x0 = 24
        x = x0
        row_h = 38  # un poco más alto
        for col, w in zip(columns, col_widths):
            draw.rectangle([(x, y), (x + w, y + row_h)], fill=(242, 223, 227), outline=color_border)
            draw_text_upper(draw, (x + 5, y + 10), col, fill=color_primary_dark, font=fonts["table_header"])
            x += w

        for i, fila in enumerate(filas, start=1):
            row_y = y + i * row_h
            x = x0
            values = [
                fila.agente,
                fila.eps,
                fila.estado,
                self._fmt_nullable(fila.kpi_hrs_live),
                self._seconds_to_hhmmss(fila.hrs_efectivas_seg),
                self._fmt_nullable(fila.adherencia),
                str(fila.visualizaciones_totales),
                self._fmt_nullable(fila.visualizaciones_promedio),
                str(fila.espectadores_unicos),
                str(fila.espectadores_activos),
                self._seconds_to_hhmmss(fila.duracion_media_visualizacion_seg),
                str(fila.peak_espectadores_simultaneos),
                self._fmt_nullable(fila.factor),
                "SI" if fila.excel_subido else "NO",
            ]
            fill = color_card if i % 2 else color_bg
            for value, w in zip(values, col_widths):
                draw.rectangle([(x, row_y), (x + w, row_y + row_h)], fill=fill, outline=color_border)
                draw.text((x + 5, row_y + 10), str(value)[:22], fill=color_text, font=fonts["table_cell"])
                x += w

        # Tabla de tramos
        tramo_top = y + (len(filas) + 2) * row_h + 35
        draw_text_upper(
            draw,
            (24, tramo_top - 30),
            "Cobertura por tramo horario (inicio live) y promedio visualizaciones",
            fill=color_primary_dark,
            font=fonts["section"],
        )

        tramo_columns = [
            "AGENTE", "11-14 LIVES", "11-14 VIS PROM", "14-17 LIVES", "14-17 VIS PROM",
            "17-20 LIVES", "17-20 VIS PROM", "PEAK MAX", "FACTOR"
        ]
        tramo_col_widths = [180, 130, 140, 130, 140, 130, 140, 110, 90]

        x = x0
        for col, w in zip(tramo_columns, tramo_col_widths):
            draw.rectangle([(x, tramo_top), (x + w, tramo_top + row_h)], fill=(242, 223, 227), outline=color_border)
            draw_text_upper(draw, (x + 5, tramo_top + 10), col, fill=color_primary_dark, font=fonts["table_header"])
            x += w

        for i, fila in enumerate(filas, start=1):
            row_y = tramo_top + i * row_h
            x = x0
            values = [
                fila.agente,
                str(fila.lives_por_tramo["11-14"]),
                self._fmt_nullable(fila.vis_promedio_por_tramo["11-14"]),
                str(fila.lives_por_tramo["14-17"]),
                self._fmt_nullable(fila.vis_promedio_por_tramo["14-17"]),
                str(fila.lives_por_tramo["17-20"]),
                self._fmt_nullable(fila.vis_promedio_por_tramo["17-20"]),
                str(fila.peak_espectadores_simultaneos),
                self._fmt_nullable(fila.factor),
            ]
            fill = color_card if i % 2 else color_bg
            for value, w in zip(values, tramo_col_widths):
                draw.rectangle([(x, row_y), (x + w, row_y + row_h)], fill=fill, outline=color_border)
                draw.text((x + 5, row_y + 10), str(value)[:22], fill=color_text, font=fonts["table_cell"])
                x += w

        # Graficos (mismos, pero usando fuentes más grandes)
        chart_y = tramo_top + (len(filas) + 2) * row_h + 30
        self._draw_bar_chart(
            draw,
            title="VISUALIZACIONES PROMEDIO POR EJECUTIVO",
            subtitle="Permite detectar quienes convierten mejor alcance por LIVE",
            x=24,
            y=chart_y,
            w=1060,
            h=320,
            labels=[f.agente for f in filas],
            values=[f.visualizaciones_promedio for f in filas],
            bar_color=(220, 51, 84),
            border=color_border,
            title_color=color_primary_dark,
            text_color=color_text,
            muted_color=color_muted,
            font_title=fonts["section"],
            font_body=fonts["small"],
        )
        self._draw_bar_chart(
            draw,
            title="PEAK DE ESPECTADORES SIMULTÁNEOS POR EJECUTIVO",
            subtitle="Compara capacidad de concentrar audiencia en su mejor LIVE del día",
            x=1110,
            y=chart_y,
            w=1060,
            h=320,
            labels=[f.agente for f in filas],
            values=[f.peak_espectadores_simultaneos for f in filas],
            bar_color=(156, 17, 54),
            border=color_border,
            title_color=color_primary_dark,
            text_color=color_text,
            muted_color=color_muted,
            font_title=fonts["section"],
            font_body=fonts["small"],
        )

        # Insights
        insight_y = chart_y + 350
        draw_text_upper(draw, (24, insight_y), "Insights accionables del dia", fill=color_primary_dark, font=fonts["section"])

        top_factor = max((f for f in filas if f.factor is not None), key=lambda f: f.factor, default=None)
        mejor_adherencia = max((f for f in filas if f.adherencia is not None), key=lambda f: f.adherencia, default=None)
        alertas_excel = [f.agente for f in filas if not f.excel_subido]

        insights = [
            f"1) Top en visualizaciones totales: {mejor_ejecutivo_vis.agente} con {mejor_ejecutivo_vis.visualizaciones_totales}.",
            f"2) Mejor factor (vis_prom / peak): {top_factor.agente} con {self._fmt_nullable(top_factor.factor)}." if top_factor else "2) Sin factor calculable para hoy.",
            f"3) Mejor adherencia (KPI/horas efectivas): {mejor_adherencia.agente} con {self._fmt_nullable(mejor_adherencia.adherencia)}." if mejor_adherencia else "3) Sin adherencia calculable para hoy.",
            f"4) Ejecutivos sin Excel de ventas/leads: {', '.join(alertas_excel) if alertas_excel else 'Ninguno'}.",
            "5) Recomendacion: replicar franja y dinamicas de los ejecutivos top en vis_prom y factor.",
        ]

        for i, insight in enumerate(insights):
            draw.text((34, insight_y + 34 + i * 26), insight, fill=color_text, font=fonts["table_cell"])

        draw.text(
            (24, height - 30),
            "NOTA: LEADS / VENTAS / %CONVERSION EN NULL HASTA INTEGRAR PROCESAMIENTO DE EXCEL.",
            fill=(155, 37, 50),
            font=fonts["small"],
        )

        image.save(path)

    @staticmethod
    def _draw_bar_chart(
        draw: ImageDraw.ImageDraw,
        title: str,
        subtitle: str,
        x: int,
        y: int,
        w: int,
        h: int,
        labels: list[str],
        values: list[float],
        bar_color: tuple[int, int, int],
        border: tuple[int, int, int],
        title_color: tuple[int, int, int],
        text_color: tuple[int, int, int],
        muted_color: tuple[int, int, int],
        font_title,
        font_body,
    ) -> None:
        draw.rounded_rectangle([(x, y), (x + w, y + h)], radius=12, outline=border, fill=(255, 255, 255))
        draw.text((x + 12, y + 10), title.upper(), fill=title_color, font=font_title)
        draw.text((x + 12, y + 40), subtitle, fill=muted_color, font=font_body)

        inner_x1 = x + 45
        inner_y1 = y + 75
        inner_x2 = x + w - 15
        inner_y2 = y + h - 40
        draw.rectangle([(inner_x1, inner_y1), (inner_x2, inner_y2)], outline=border, fill=(254, 250, 251))

        max_value = max(values, default=1) or 1
        bar_slot = max((inner_x2 - inner_x1) // max(len(values), 1), 1)

        for idx, (label, value) in enumerate(zip(labels, values)):
            bx1 = inner_x1 + idx * bar_slot + 8
            bx2 = min(bx1 + bar_slot - 16, inner_x2)
            bh = int((value / max_value) * (inner_y2 - inner_y1 - 24)) if max_value else 0
            by1 = inner_y2 - bh
            by2 = inner_y2
            draw.rectangle([(bx1, by1), (bx2, by2)], fill=bar_color)
            draw.text((bx1, by2 + 5), label[:12], fill=text_color, font=font_body)
            draw.text((bx1, max(by1 - 16, inner_y1 + 2)), str(round(value, 1)), fill=title_color, font=font_body)

        draw.text((inner_x1, inner_y1 - 16), "VALOR", fill=muted_color, font=font_body)
        draw.text((inner_x2 - 80, inner_y2 + 20), "EJECUTIVO", fill=muted_color, font=font_body)

    @staticmethod
    def _avg(values: list[float]) -> float | None:
        if not values:
            return None
        return round(sum(values) / len(values), 2)

    @staticmethod
    def _fmt_nullable(value: Any) -> str:
        if value is None:
            return "NULL"
        if isinstance(value, float):
            return f"{value:.2f}"
        return str(value)


def resolver_fecha_objetivo(fecha_objetivo: str | None) -> str:
    if fecha_objetivo:
        # Primero convertimos la entrada (suponiendo que viene como d/m/y) a objeto datetime
        # y luego la formateamos al nuevo estilo con guiones
        return datetime.strptime(fecha_objetivo, "%d/%m/%y").strftime("%d-%m-%Y")
    
    # Si no hay fecha, restamos un día y formateamos
    ayer = datetime.now() - timedelta(days=1)
    return ayer.strftime("%d-%m-%Y")