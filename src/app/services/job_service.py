from __future__ import annotations

from datetime import datetime, timedelta, time
import json
from typing import Iterable

from sqlmodel import Session, select

from src.bd.schema import Ejecutivo, ExecutiveDailySummary, JobLog, JobRun, LIVE
from src.config.engine_config import get_engine
from src.proceso_01_ocr import ejecutar_proceso_ocr

STAGES = [
    "PENDING",
    "VALIDATING_STRUCTURE",
    "DOWNLOADING_FILES",
    "OCR_IMAGES",
    "PROCESSING_EXCEL",
    "SAVING_RESULTS",
    "PROVISIONING_NEXT_DAY",
    "DONE",
    "DONE_WITH_WARNINGS",
    "ERROR",
    "NEEDS_LOGIN",
    "ERROR_OCR_PARSE",
]


class NeedsLoginError(Exception):
    pass


class JobService:
    def __init__(self):
        self.engine = get_engine()

    def create_job(self, fecha_objetivo: str) -> dict:
        fecha = datetime.strptime(fecha_objetivo, "%d/%m/%y").date()
        next_day = (fecha + timedelta(days=1)).strftime("%d/%m/%y")
        with Session(self.engine) as session:
            job = JobRun(fecha_objetivo=fecha_objetivo, fecha_siguiente=next_day)
            session.add(job)
            session.commit()
            session.refresh(job)
            self._log(session, job.id, "PENDING", "Job creado")
            session.commit()
            return {
                "id": job.id,
                "status": job.status,
                "fecha_objetivo": job.fecha_objetivo,
                "fecha_siguiente": job.fecha_siguiente,
            }

    def _set_status(self, session: Session, job: JobRun, status: str) -> None:
        job.status = status
        job.updated_at = datetime.utcnow()
        session.add(job)

    def _log(self, session: Session, job_id: int, stage: str, message: str, level: str = "INFO") -> None:
        session.add(JobLog(job_id=job_id, stage=stage, message=message, level=level))

    def append_warnings(self, session: Session, job: JobRun, warnings: Iterable[str]) -> None:
        current = json.loads(job.warnings_json)
        current.extend(warnings)
        job.warnings_json = json.dumps(current, ensure_ascii=False)
        session.add(job)

    def run_pipeline(self, job_id: int) -> None:
        with Session(self.engine) as session:
            job = session.get(JobRun, job_id)
            if not job:
                return
            warnings: list[str] = []
            try:
                for status, msg in [
                    ("VALIDATING_STRUCTURE", "Validando estructura en Drive para fecha objetivo"),
                    ("DOWNLOADING_FILES", "Descargando imágenes y excels por ejecutivo"),
                ]:
                    self._set_status(session, job, status)
                    self._log(session, job.id, status, msg)
                    session.commit()

                self._set_status(session, job, "OCR_IMAGES")
                self._log(session, job.id, "OCR_IMAGES", "Ejecutando orquestador OCR real (ejecutar_proceso_ocr)")
                session.commit()
                ocr_result = ejecutar_proceso_ocr(fecha_objetivo=job.fecha_objetivo, full_scan=False)
                warnings.extend(ocr_result.get("warnings", []))
                if ocr_result.get("errors"):
                    warnings.extend(ocr_result["errors"])
                self._log(
                    session,
                    job.id,
                    "OCR_IMAGES",
                    f"OCR procesadas={ocr_result.get('processed', 0)} guardadas={ocr_result.get('saved', 0)}",
                )
                session.commit()

                for status, msg in [
                    ("PROCESSING_EXCEL", "Procesando reglas de negocio de Excel"),
                    ("SAVING_RESULTS", "Persistiendo métricas LIVE y resumen diario"),
                    ("PROVISIONING_NEXT_DAY", "Provisionando carpetas para fecha siguiente"),
                ]:
                    self._set_status(session, job, status)
                    self._log(session, job.id, status, msg)
                    session.commit()

                self._upsert_daily_summaries(session, job)

                if warnings:
                    self.append_warnings(session, job, warnings)
                    self._set_status(session, job, "DONE_WITH_WARNINGS")
                else:
                    self._set_status(session, job, "DONE")
                self._log(session, job.id, job.status, "Pipeline finalizado")
                session.commit()
            except NeedsLoginError:
                self._set_status(session, job, "NEEDS_LOGIN")
                self._log(session, job.id, "NEEDS_LOGIN", "Token de Drive expirado/revocado", level="WARNING")
                session.commit()
            except Exception as exc:  # noqa: BLE001
                self._set_status(session, job, "ERROR")
                self._log(session, job.id, "ERROR", f"Error inesperado: {exc}", level="ERROR")
                session.commit()

    def _upsert_daily_summaries(self, session: Session, job: JobRun) -> None:
        fecha = datetime.strptime(job.fecha_objetivo, "%d/%m/%y").date()
        ejecutivos = session.exec(select(Ejecutivo)).all()
        for ejecutivo in ejecutivos:
            existing = session.exec(
                select(ExecutiveDailySummary).where(
                    ExecutiveDailySummary.ejecutivo_id == ejecutivo.id,
                    ExecutiveDailySummary.fecha == fecha,
                )
            ).first()
            if existing:
                if existing.leads is None or existing.ventas is None:
                    existing.warnings = self._merge_warning(existing.warnings, "Excel no encontrado para la fecha objetivo")
                    session.add(existing)
                continue
            summary = ExecutiveDailySummary(
                ejecutivo_id=ejecutivo.id,
                fecha=fecha,
                leads=None,
                ventas=None,
                total_rows=None,
                warnings="Excel no encontrado para la fecha objetivo",
            )
            session.add(summary)

    @staticmethod
    def _merge_warning(existing: str | None, new_warning: str) -> str:
        if not existing:
            return new_warning
        if new_warning in existing:
            return existing
        return f"{existing}; {new_warning}"

    @staticmethod
    def _time_to_hours(value: time | None) -> float:
        if value is None:
            return 0.0
        return (value.hour * 3600 + value.minute * 60 + value.second) / 3600

    @staticmethod
    def _safe_ratio(numerator: int | float | None, denominator: int | float | None) -> float | None:
        if numerator is None or denominator is None or denominator == 0:
            return None
        return round(float(numerator) / float(denominator), 4)

    def list_jobs(self) -> list[JobRun]:
        with Session(self.engine) as session:
            return list(session.exec(select(JobRun).order_by(JobRun.id.desc())).all())

    def get_job(self, job_id: int) -> JobRun | None:
        with Session(self.engine) as session:
            return session.get(JobRun, job_id)

    def get_logs(self, job_id: int) -> list[JobLog]:
        with Session(self.engine) as session:
            return list(session.exec(select(JobLog).where(JobLog.job_id == job_id).order_by(JobLog.id)).all())

    def report_daily(self, date_str: str) -> dict:
        fecha = datetime.strptime(date_str, "%d/%m/%y").date()
        with Session(self.engine) as session:
            ejecutivos = list(session.exec(select(Ejecutivo).order_by(Ejecutivo.nombre)).all())
            summaries = {
                summary.ejecutivo_id: summary
                for summary in session.exec(
                    select(ExecutiveDailySummary).where(ExecutiveDailySummary.fecha == fecha)
                ).all()
            }
            live_rows = session.exec(
                select(LIVE).where(LIVE.fecha_live == fecha)
            ).all()

        live_by_exec: dict[int, dict] = {}
        for live in live_rows:
            bucket = live_by_exec.setdefault(
                live.ejecutivo_id,
                {
                    "horas_efectivas": 0.0,
                    "visualizaciones": 0,
                    "espectadores_unicos": 0,
                    "espectadores_activos": 0,
                    "duracion_media_visualizacion_horas": 0.0,
                    "duracion_media_count": 0,
                    "peak_espectadores": 0,
                },
            )
            bucket["horas_efectivas"] += self._time_to_hours(live.duracion_live)
            bucket["visualizaciones"] += live.visualizaciones or 0
            bucket["espectadores_unicos"] += live.espectadores_unicos or 0
            bucket["espectadores_activos"] += live.espectadores_activos or 0
            if live.duracion_media_visualizacion:
                bucket["duracion_media_visualizacion_horas"] += self._time_to_hours(live.duracion_media_visualizacion)
                bucket["duracion_media_count"] += 1
            bucket["peak_espectadores"] = max(bucket["peak_espectadores"], live.pico_espectadores_simultaneos or 0)

        rows = []
        for ejecutivo in ejecutivos:
            hrs_live = 2.0
            live_info = live_by_exec.get(
                ejecutivo.id,
                {
                    "horas_efectivas": 0.0,
                    "visualizaciones": 0,
                    "espectadores_unicos": 0,
                    "espectadores_activos": 0,
                    "duracion_media_visualizacion_horas": 0.0,
                    "duracion_media_count": 0,
                    "peak_espectadores": 0,
                },
            )
            summary = summaries.get(ejecutivo.id)
            leads = summary.leads if summary else None
            ventas = summary.ventas if summary else None
            warning = summary.warnings if summary and summary.warnings else "Excel no encontrado para la fecha objetivo"

            duracion_media = None
            if live_info["duracion_media_count"] > 0:
                duracion_media = round(
                    live_info["duracion_media_visualizacion_horas"] / live_info["duracion_media_count"],
                    4,
                )

            rows.append(
                {
                    "fecha": date_str,
                    "eps": ejecutivo.eps or "PHOENIX",
                    "agente": ejecutivo.nombre,
                    "estado_agente": ejecutivo.estado,
                    "hrs_live": hrs_live,
                    "horas_efectivas": round(live_info["horas_efectivas"], 4),
                    "adherencia": self._safe_ratio(live_info["horas_efectivas"], hrs_live),
                    "leads": leads,
                    "ventas": ventas,
                    "conversion": self._safe_ratio(ventas, leads),
                    "visualizaciones": live_info["visualizaciones"],
                    "espectadores_unicos": live_info["espectadores_unicos"],
                    "espectadores_activos": live_info["espectadores_activos"],
                    "duracion_media_visualizacion": duracion_media,
                    "peak_espectadores": live_info["peak_espectadores"],
                    "warnings": warning,
                }
            )

        total_leads = sum(row["leads"] or 0 for row in rows)
        total_ventas = sum(row["ventas"] or 0 for row in rows)
        total_visualizaciones = sum(row["visualizaciones"] for row in rows)

        return {
            "fecha": date_str,
            "totales": {
                "leads": total_leads,
                "ventas": total_ventas,
                "conversion_global": self._safe_ratio(total_ventas, total_leads),
                "visualizaciones": total_visualizaciones,
                "agentes": len(rows),
            },
            "rows": rows,
        }
