from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.app.api.routes import router as mvp_router
from src.backend.routes import routes as legacy_routes
from src.bd.inicializacion.bd_init import inicializar_bd_sqlite
from src.config.log_config import configurar_log

configurar_log()
inicializar_bd_sqlite()

app = FastAPI(title="TikTok Live Control Diario", version="0.2.0", docs_url="/swagger")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(legacy_routes.router)
app.include_router(mvp_router)
