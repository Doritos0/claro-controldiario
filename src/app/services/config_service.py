from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
import os

APP_NAME = "TikTokLiveApp"


@dataclass
class AppConfig:
    root_folder_id: str = ""
    drive_token_path: str = ""
    ollama_base_url: str = "http://192.168.1.52:11434"
    ollama_model: str = "qwen2.5vl:7b"
    auto_provision_next_day: bool = True
    policy_missing_target_date: str = "WARN_AND_CONTINUE"


def _get_base_config_dir() -> Path:
    windows_appdata = os.getenv("APPDATA")
    if windows_appdata:
        return Path(windows_appdata)
    return Path.home() / ".config"


def get_config_path() -> Path:
    config_dir = _get_base_config_dir() / APP_NAME
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config.json"


def load_config() -> AppConfig:
    config_path = get_config_path()
    if not config_path.exists():
        cfg = AppConfig()
        save_config(cfg)
        return cfg

    raw = json.loads(config_path.read_text(encoding="utf-8"))
    return AppConfig(**{**asdict(AppConfig()), **raw})


def save_config(config: AppConfig) -> None:
    config_path = get_config_path()
    config_path.write_text(json.dumps(asdict(config), indent=2, ensure_ascii=False), encoding="utf-8")
