from __future__ import annotations

from datetime import datetime, timedelta
import json
from typing import Iterable

from sqlmodel import Session, select

from src.bd.schema import Ejecutivo, ExecutiveDailySummary, JobLog, JobRun, LIVE
from src.config.engine_config import get_engine

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
                    ("OCR_IMAGES", "Procesando OCR de imágenes con Ollama Qwen2.5VL"),
                    ("PROCESSING_EXCEL", "Procesando reglas de negocio de Excel"),
                    ("SAVING_RESULTS", "Persistiendo métricas LIVE y resumen diario"),
                    ("PROVISIONING_NEXT_DAY", "Provisionando carpetas para fecha siguiente"),
                ]:
                    self._set_status(session, job, status)
                    self._log(session, job.id, status, msg)
                    session.commit()

                # MVP: placeholder warnings until Drive/OCR adapters are wired.
                warnings.append("MVP: Integración Drive/OCR en modo scaffold; conectar servicios productivos.")
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
                continue
            summary = ExecutiveDailySummary(
                ejecutivo_id=ejecutivo.id,
                fecha=fecha,
                leads=None,
                ventas=None,
                total_rows=None,
                warnings="Pendiente carga Excel real",
            )
            session.add(summary)

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
            summaries = session.exec(
                select(ExecutiveDailySummary, Ejecutivo)
                .join(Ejecutivo, Ejecutivo.id == ExecutiveDailySummary.ejecutivo_id)
                .where(ExecutiveDailySummary.fecha == fecha)
            ).all()
            live_rows = session.exec(
                select(LIVE, Ejecutivo)
                .join(Ejecutivo, Ejecutivo.id == LIVE.ejecutivo_id)
                .where(LIVE.fecha_live == fecha)
            ).all()

        exec_items = [
            {
                "ejecutivo": ejecutivo.nombre,
                "leads": summary.leads,
                "ventas": summary.ventas,
                "total_rows": summary.total_rows,
                "warnings": summary.warnings,
            }
            for summary, ejecutivo in summaries
        ]

        total_leads = sum(item["leads"] or 0 for item in exec_items)
        total_ventas = sum(item["ventas"] or 0 for item in exec_items)

        top_visualizaciones = sorted(
            [
                {
                    "ejecutivo": ejecutivo.nombre,
                    "visualizaciones": live.visualizaciones or 0,
                    "hora_inicio": str(live.hora_inicio) if live.hora_inicio else None,
                }
                for live, ejecutivo in live_rows
            ],
            key=lambda x: x["visualizaciones"],
            reverse=True,
        )[:5]

        return {
            "fecha": date_str,
            "totales": {
                "leads": total_leads,
                "ventas": total_ventas,
                "lives": len(live_rows),
            },
            "ejecutivos": exec_items,
            "top_live_vistas": top_visualizaciones,
        }
