import json
from datetime import datetime, timedelta
from urllib import request

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.bd.bd_configuracion import ConfiguracionService
from src.bd.bd_ejecutivo import EjecutivoService
from src.bd.bd_usuario import UsuarioService
from src.reportes.dashboard_diario_service import DashboardDiarioService, resolver_fecha_objetivo
from src.whatsapp.local_image_service import LocalImageService
from src.bd.inicializacion.bd_init import inicializar_bd_sqlite

router = APIRouter(tags=["web"])
inicializar_bd_sqlite()


@router.get("/test", operation_id="Peticion_test", response_model=str)
def test() -> str:
    return "Funciona"


class LoginRequest(BaseModel):
    user: str
    password: str


class LoginResponse(BaseModel):
    user_id: int
    empresa_id: int
    user: str


class EjecutivoRest(BaseModel):
    nombre: str
    estado: str
    eps: str
    user_id: int


class ConfiguracionRest(BaseModel):
    user_id: int
    grupo_wsp: str


class ReporteRequest(BaseModel):
    user_id: int
    fecha: str | None = None


@router.post('/auth/login', response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    usuario = UsuarioService().autenticar(payload.user, payload.password)
    if not usuario:
        raise HTTPException(status_code=401, detail='Credenciales inválidas')
    return LoginResponse(user_id=usuario.id, empresa_id=usuario.empresa_id, user=usuario.user)


@router.get('/configuracion/{user_id}')
def get_configuracion(user_id: int):
    configuracion = ConfiguracionService().get_por_usuario(user_id)
    return {
        'exists': configuracion is not None,
        'grupo_wsp': configuracion.grupo_wsp if configuracion else None,
    }


@router.post('/configuracion')
def upsert_configuracion(payload: ConfiguracionRest):
    configuracion = ConfiguracionService().upsert(payload.user_id, payload.grupo_wsp)
    return {'id': configuracion.id, 'grupo_wsp': configuracion.grupo_wsp}


@router.post('/ejecutivos', operation_id='crear_ejecutivo', response_model=int)
def crear_ejecutivo(payload: EjecutivoRest) -> int:
    usuario = next((u for u in UsuarioService().get_usuarios_sql() if u.id == payload.user_id), None)
    if not usuario:
        raise HTTPException(status_code=404, detail='Usuario no encontrado')

    ejecutivo_creado = EjecutivoService().guardar_ejecutivo_sql(
        nombre=payload.nombre,
        estado=payload.estado,
        eps=payload.eps,
        empresa_id=usuario.empresa_id,
    )
    return ejecutivo_creado.id


def _post_json(url: str, data: dict):
    req = request.Request(url, method='POST', data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
    with request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode('utf-8'))


@router.post('/reporte/generar')
def generar_reporte(payload: ReporteRequest):
    usuario = next((u for u in UsuarioService().get_usuarios_sql() if u.id == payload.user_id), None)
    if not usuario:
        raise HTTPException(status_code=404, detail='Usuario no encontrado')

    config = ConfiguracionService().get_por_usuario(payload.user_id)
    if not config:
        raise HTTPException(status_code=400, detail='Usuario sin configuración de grupo WhatsApp')

    fecha = payload.fecha or (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    fecha_wsp = LocalImageService.normalizar_fecha_iso(fecha)

    try:
        _post_json('http://localhost:3100/descargar-imagenes', {'nombre_grupo': config.grupo_wsp, 'fecha': fecha_wsp})
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f'Error descargando imágenes desde express: {exc}')

    procesadas = LocalImageService().procesar_carpeta_fecha(fecha_wsp, usuario.empresa_id)
    dashboard = DashboardDiarioService().generar_dashboard_diario(resolver_fecha_objetivo(fecha_wsp), empresa_id=usuario.empresa_id)

    return {'procesadas': procesadas, 'dashboard_path': str(dashboard) if dashboard else None}


@router.post('/reporte/consolidado')
def reporte_consolidado(payload: ReporteRequest):
    usuario = next((u for u in UsuarioService().get_usuarios_sql() if u.id == payload.user_id), None)
    if not usuario:
        raise HTTPException(status_code=404, detail='Usuario no encontrado')

    fecha = payload.fecha or (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
    filas = DashboardDiarioService()._obtener_filas(fecha_objetivo=fecha_obj, empresa_id=usuario.empresa_id)
    return [fila.__dict__ for fila in filas]


@router.post('/whatsapp/iniciar-session')
def iniciar_session_whatsapp():
    try:
        return _post_json('http://localhost:3100/iniciar-session', {})
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f'No se pudo iniciar sesión WhatsApp: {exc}')


@router.get('/whatsapp/iniciar-session')
def estado_session_whatsapp():
    try:
        with request.urlopen('http://localhost:3100/iniciar-session', timeout=20) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f'No se pudo consultar sesión WhatsApp: {exc}')
