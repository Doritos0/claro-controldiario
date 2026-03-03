from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path


APP_DIR_NAME = "ClaroControlDiario"


def get_resource_path(relative_path: str) -> Path:
    """
    Ruta de recursos de solo lectura (bundle PyInstaller o repo local).
    """
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    return base_path / relative_path


def get_app_home_dir() -> Path:
    local_app_data = os.getenv("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / APP_DIR_NAME
    return Path.home() / f".{APP_DIR_NAME.lower()}"


def _copy_resource_to_app_home(relative_path: str, app_home: Path) -> Path | None:
    src = get_resource_path(relative_path)
    if not src.exists():
        return None

    dst = app_home / relative_path
    dst.parent.mkdir(parents=True, exist_ok=True)

    if src.is_dir():
        if not dst.exists():
            shutil.copytree(src, dst)
    else:
        if not dst.exists():
            shutil.copy2(src, dst)
    return dst


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _apply_runtime_env_from_config(app_home: Path) -> None:
    cfg_path = app_home / "app_config.json"
    cfg = _load_json(cfg_path)

    mapping = {
        "google_drive_root_folder_id": "GOOGLE_DRIVE_ROOT_FOLDER_ID",
        "google_drive_credentials_path": "GOOGLE_DRIVE_CREDENTIALS_PATH",
        "gemini_api_key": "GEMINI_API_KEY",
        "gemini_model_ocr": "GEMINI_MODEL_OCR",
        "ambiente": "AMBIENTE",
        "bd_name": "BD_NAME",
    }

    for cfg_key, env_key in mapping.items():
        if os.getenv(env_key):
            continue
        value = cfg.get(cfg_key)
        if isinstance(value, str) and value.strip():
            os.environ[env_key] = value.strip()


def _ensure_db_ready() -> None:
    from sqlmodel import Session, select

    from src.bd.inicializacion.bd_init import inicializar_bd_sqlite
    from src.bd.inicializacion.bd_datos import inicializar_datos
    from src.bd.schema import Ejecutivo, Usuario
    from src.config.engine_config import get_engine

    inicializar_bd_sqlite()

    engine = get_engine()
    with Session(engine) as session:
        has_exec = session.exec(select(Ejecutivo).limit(1)).first() is not None
        has_users = session.exec(select(Usuario).limit(1)).first() is not None

    if not has_exec or not has_users:
        inicializar_datos()


def bootstrap_runtime() -> Path:
    app_home = get_app_home_dir()
    app_home.mkdir(parents=True, exist_ok=True)

    # Activos read-only empaquetados
    _copy_resource_to_app_home("CLARO-TIKTOK.db", app_home)
    _copy_resource_to_app_home("credentials.json", app_home)
    _copy_resource_to_app_home("app_config.json", app_home)
    _copy_resource_to_app_home("settings.yaml", app_home)
    _copy_resource_to_app_home("client_secret.json", app_home)
    _copy_resource_to_app_home("src/docs", app_home)

    os.environ.setdefault("AMBIENTE", "sqlite")

    db_path = app_home / "CLARO-TIKTOK.db"
    if not db_path.exists():
        db_path.touch()
    os.environ["BD_PATH"] = str(db_path)

    os.chdir(app_home)
    _apply_runtime_env_from_config(app_home)
    _ensure_db_ready()
    return app_home
