import os
from pathlib import Path


def _default_app_data_dir() -> Path:
    local_app_data = os.getenv("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "ClaroControlDiario"

    return Path.home() / ".claro-control-diario"


def get_app_data_dir() -> Path:
    app_data = os.getenv("APP_DATA_DIR")
    path = Path(app_data) if app_data else _default_app_data_dir()
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_downloads_dir() -> Path:
    custom_downloads = os.getenv("DOWNLOADS_DIR")
    downloads_dir = Path(custom_downloads) if custom_downloads else get_app_data_dir() / "descargas"
    downloads_dir.mkdir(parents=True, exist_ok=True)
    return downloads_dir
