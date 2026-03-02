from __future__ import annotations

from datetime import date, timedelta
import json

from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from src.app.services.job_service import JobService
from src.app.services.config_service import load_config
from src.bd.bd_ejecutivo import EjecutivoService

router = APIRouter(tags=["mvp"])
job_service = JobService()


class RunRequest(BaseModel):
    fecha_objetivo: str | None = None
    full_scan: bool = False


class EjecutivoCreate(BaseModel):
    nombre: str
    estado: str = "ACTIVO"
    eps: str = "CLARO"


@router.post("/run")
def run_job(payload: RunRequest, background_tasks: BackgroundTasks) -> dict:
    fecha = payload.fecha_objetivo or (date.today() - timedelta(days=1)).strftime("%d/%m/%y")
    job = job_service.create_job(fecha)
    background_tasks.add_task(job_service.run_pipeline, job["id"])
    return {"job_id": job["id"], "status": job["status"], "fecha_objetivo": fecha}


@router.get("/jobs")
def list_jobs() -> list[dict]:
    jobs = job_service.list_jobs()
    return [
        {
            "id": job.id,
            "status": job.status,
            "fecha_objetivo": job.fecha_objetivo,
            "fecha_siguiente": job.fecha_siguiente,
            "warnings": json.loads(job.warnings_json),
        }
        for job in jobs
    ]


@router.get("/jobs/{job_id}")
def get_job(job_id: int) -> dict:
    job = job_service.get_job(job_id)
    if not job:
        return {"error": "not_found"}
    return {
        "id": job.id,
        "status": job.status,
        "fecha_objetivo": job.fecha_objetivo,
        "fecha_siguiente": job.fecha_siguiente,
        "warnings": json.loads(job.warnings_json),
    }


@router.get("/jobs/{job_id}/logs")
def get_job_logs(job_id: int) -> list[dict]:
    logs = job_service.get_logs(job_id)
    return [{"stage": l.stage, "level": l.level, "message": l.message, "created_at": l.created_at.isoformat()} for l in logs]


@router.post("/drive/reauth")
def drive_reauth() -> dict:
    config = load_config()
    return {
        "status": "READY_FOR_OAUTH",
        "message": "Abrir navegador externo para OAuth callback localhost",
        "token_path": config.drive_token_path,
    }


@router.post("/mvp/ejecutivos")
def create_executivo(payload: EjecutivoCreate) -> dict:
    service = EjecutivoService()
    ejecutivo = service.guardar_ejecutivo_sql(payload.nombre, payload.estado, payload.eps)
    return {"id": ejecutivo.id, "nombre": ejecutivo.nombre}


@router.get("/reports/daily")
def report_daily(date: str) -> dict:  # noqa: A002
    return job_service.report_daily(date)


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard() -> str:
    report = job_service.report_daily((date.today() - timedelta(days=1)).strftime("%d/%m/%y"))
    rows = "".join(
        f"<tr><td>{item['ejecutivo']}</td><td>{item['leads']}</td><td>{item['ventas']}</td><td>{item['warnings'] or ''}</td></tr>"
        for item in report["ejecutivos"]
    )
    top_rows = "".join(
        f"<li>{item['ejecutivo']} - {item['visualizaciones']} vistas (inicio {item['hora_inicio'] or 'N/A'})</li>"
        for item in report["top_live_vistas"]
    )
    return f"""
    <html><body>
    <h1>Dashboard TikTok Live (MVP)</h1>
    <p>Fecha: {report['fecha']}</p>
    <p>Leads globales: {report['totales']['leads']} | Ventas globales: {report['totales']['ventas']} | Lives: {report['totales']['lives']}</p>
    <h2>Resumen por ejecutivo</h2>
    <table border='1' cellpadding='5'>
      <tr><th>Ejecutivo</th><th>Leads</th><th>Ventas</th><th>Warnings</th></tr>
      {rows}
    </table>
    <h2>Top vistas LIVE</h2><ul>{top_rows}</ul>
    </body></html>
    """
