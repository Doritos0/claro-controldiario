from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from sqlmodel import Session, select


def _app_home_dir() -> Path:
    local_app_data = os.getenv("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "ControlDiarioClaro"
    return Path.home() / ".control_diario_claro"


def _bundled_candidate_paths(filename: str) -> list[Path]:
    candidates: list[Path] = []
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        candidates.append(exe_dir / filename)
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidates.append(Path(meipass) / filename)
    candidates.append(Path.cwd() / filename)
    candidates.append(Path(__file__).resolve().parents[1] / filename)
    return candidates


def _copy_if_exists(filename: str, dest_dir: Path) -> Path | None:
    for src in _bundled_candidate_paths(filename):
        if src.exists():
            dest = dest_dir / filename
            if not dest.exists():
                shutil.copy2(src, dest)
            return dest
    return None


def _ensure_db_ready(db_path: Path) -> None:
    from src.bd.inicializacion.bd_init import inicializar_bd_sqlite
    from src.bd.inicializacion.bd_datos import inicializar_datos
    from src.bd.schema import Ejecutivo
    from src.config.engine_config import get_engine

    inicializar_bd_sqlite()

    engine = get_engine()
    with Session(engine) as session:
        has_exec = session.exec(select(Ejecutivo).limit(1)).first() is not None

    if not has_exec:
        inicializar_datos()


def bootstrap_runtime() -> Path:
    app_home = _app_home_dir()
    app_home.mkdir(parents=True, exist_ok=True)

    os.environ.setdefault("AMBIENTE", "sqlite")

    db_path = app_home / "CLARO-TIKTOK.db"
    os.environ["BD_PATH"] = str(db_path)

    if not db_path.exists():
        seeded = _copy_if_exists("CLARO-TIKTOK.db", app_home)
        if seeded is None:
            db_path.touch()

    _copy_if_exists("credentials.json", app_home)
    _copy_if_exists("app_config.json", app_home)

    # Ajustar cwd para que artifacts/ y otros archivos queden en carpeta de app
    os.chdir(app_home)

    _ensure_db_ready(db_path)
    return app_home
