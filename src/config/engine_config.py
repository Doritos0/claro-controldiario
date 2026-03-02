from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from sqlalchemy import Engine, create_engine

APP_NAME = "TikTokLiveApp"
DB_FILENAME = "CLARO-TIKTOK.db"


def get_appdata_dir() -> Path:
    appdata = Path.home() / ".config"
    return appdata / APP_NAME


def get_db_path() -> Path:
    env_override = Path.cwd() / DB_FILENAME
    if env_override.exists():
        return env_override
    appdata_dir = get_appdata_dir()
    appdata_dir.mkdir(parents=True, exist_ok=True)
    return appdata_dir / DB_FILENAME


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    db_path = get_db_path()
    url = f"sqlite:///{db_path}"
    return create_engine(url, connect_args={"check_same_thread": False})
