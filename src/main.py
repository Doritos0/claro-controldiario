from pathlib import Path
from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

from src.config.log_config import configurar_log

local_path = Path(__file__).parent

env_file = local_path.parent / ".env"

print(f"env_path: {env_file}")
load_dotenv(env_file)

configurar_log()

title = "Sandbox Numero WABAPI"
version = "0.0.1"

app = FastAPI(title=title, version=version, docs_url="/swagger", root_path="/api")

from src.backend.routes import routes

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods = ["*"], allow_headers=["*"])

app.include_router(routes.router)