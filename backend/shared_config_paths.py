"""Resolve shared runtime config file locations across services."""
from __future__ import annotations

import os
import shutil
from pathlib import Path


_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_SHARED_CONFIG_DIR = _PROJECT_ROOT / "uploads" / "config"
_SHARED_CONFIG_DIR_ENV = "RAGMIND_SHARED_CONFIG_DIR"
_APP_CONFIG_PATH_ENV = "RAGMIND_APP_CONFIG_PATH"
_BOT_CONFIG_PATH_ENV = "RAGMIND_BOT_CONFIG_PATH"
_LEGACY_APP_CONFIG_PATH = _PROJECT_ROOT / "app_config.json"
_LEGACY_BOT_CONFIG_PATH = _PROJECT_ROOT / "bot_config.json"


def _resolve_base_path(raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return path
    return (_PROJECT_ROOT / path).resolve()


def _resolve_config_path(*, filename: str, explicit_path_env: str) -> Path:
    explicit_path = (os.getenv(explicit_path_env) or "").strip()
    if explicit_path:
        return _resolve_base_path(explicit_path)

    shared_dir = (os.getenv(_SHARED_CONFIG_DIR_ENV) or "").strip()
    if shared_dir:
        return _resolve_base_path(shared_dir) / filename

    return _DEFAULT_SHARED_CONFIG_DIR / filename


def _ensure_shared_copy(config_path: Path, legacy_path: Path) -> Path:
    if config_path.exists() or config_path == legacy_path or not legacy_path.exists():
        return config_path

    config_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copyfile(legacy_path, config_path)
    except OSError:
        return config_path

    return config_path


def get_app_config_path() -> Path:
    config_path = _resolve_config_path(filename="app_config.json", explicit_path_env=_APP_CONFIG_PATH_ENV)
    return _ensure_shared_copy(config_path, _LEGACY_APP_CONFIG_PATH)


def get_bot_config_path() -> Path:
    config_path = _resolve_config_path(filename="bot_config.json", explicit_path_env=_BOT_CONFIG_PATH_ENV)
    return _ensure_shared_copy(config_path, _LEGACY_BOT_CONFIG_PATH)
