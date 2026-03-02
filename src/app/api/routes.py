from __future__ import annotations

from datetime import date as date_module, timedelta
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
    eps: str = "PHOENIX"


@router.post("/run")
def run_job(payload: RunRequest, background_tasks: BackgroundTasks) -> dict:
    fecha = payload.fecha_objetivo or (date_module.today() - timedelta(days=1)).strftime("%d/%m/%y")
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
def dashboard(date: str | None = None) -> str:  # noqa: A002
    selected_date = date or (date_module.today() - timedelta(days=1)).strftime("%d/%m/%y")
    report = job_service.report_daily(selected_date)
    rows = "".join(
        "<tr>"
        f"<td>{item['fecha']}</td>"
        f"<td>{item['eps']}</td>"
        f"<td>{item['agente']}</td>"
        f"<td>{item['estado_agente']}</td>"
        f"<td>{item['hrs_live']}</td>"
        f"<td>{item['horas_efectivas']}</td>"
        f"<td>{item['adherencia'] if item['adherencia'] is not None else 'N/A'}</td>"
        f"<td>{item['leads'] if item['leads'] is not None else 'N/A'}</td>"
        f"<td>{item['ventas'] if item['ventas'] is not None else 'N/A'}</td>"
        f"<td>{item['conversion'] if item['conversion'] is not None else 'N/A'}</td>"
        f"<td>{item['visualizaciones']}</td>"
        f"<td>{item['espectadores_unicos']}</td>"
        f"<td>{item['espectadores_activos']}</td>"
        f"<td>{item['duracion_media_visualizacion'] if item['duracion_media_visualizacion'] is not None else 'N/A'}</td>"
        f"<td>{item['peak_espectadores']}</td>"
        f"<td>{item['warnings'] or ''}</td>"
        "</tr>"
        for item in report["rows"]
    )
    return f"""
    <html><body>
    <form method='get' action='/dashboard'>
      <label>Fecha (DD/MM/YY):</label>
      <input name='date' value='{selected_date}' />
      <button type='submit'>Ver</button>
    </form>
    <h1>Dashboard TikTok Live (MVP)</h1>
    <p>Fecha: {report['fecha']}</p>
    <p>Leads globales: {report['totales']['leads']} | Ventas globales: {report['totales']['ventas']} | Conversión global: {report['totales']['conversion_global'] if report['totales']['conversion_global'] is not None else 'N/A'} | Visualizaciones globales: {report['totales']['visualizaciones']} | Agentes: {report['totales']['agentes']}</p>
    <table border='1' cellpadding='5'>
      <tr>
        <th>FECHA</th><th>EPS</th><th>AGENTE</th><th>ESTADO AGENTE</th><th>HRS. LIVE</th>
        <th>HORAS EFECTIVAS</th><th>Adherencia</th><th>Leads</th><th>Ventas</th><th>Conversión</th>
        <th>Visualizaciones</th><th>Espectadores Unicos</th><th>EspectadoresActivos</th>
        <th>Duración Media deVisualización</th><th>Peak Espectadores</th><th>Warnings</th>
      </tr>
      {rows}
    </table>
    </body></html>
    """
