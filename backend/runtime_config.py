"""
Runtime configuration storage.
Stores provider selections in a JSON file without requiring an app restart.
"""
from __future__ import annotations

from typing import Any, Dict
import json
import time

from backend.shared_config_paths import get_app_config_path


_cache: Dict[str, Any] = {}
_cache_ts: float = 0.0
_CACHE_TTL: float = 2.0  # seconds


def load_runtime_config() -> Dict[str, Any]:
    global _cache, _cache_ts
    config_path = get_app_config_path()
    now = time.monotonic()
    if _cache and (now - _cache_ts) < _CACHE_TTL:
        return _cache
    if not config_path.exists():
        _cache, _cache_ts = {}, now
        return _cache
    try:
        with config_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
            _cache = data if isinstance(data, dict) else {}
    except Exception:
        _cache = {}
    _cache_ts = now
    return _cache


def save_runtime_config(config: Dict[str, Any]) -> None:
    global _cache, _cache_ts
    config_path = get_app_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w", encoding="utf-8") as handle:
        json.dump(config, handle, indent=2)
    _cache = config.copy()
    _cache_ts = time.monotonic()


def update_runtime_config(updates: Dict[str, Any]) -> Dict[str, Any]:
    config = load_runtime_config()
    config.update(updates)
    save_runtime_config(config)
    return config


def get_runtime_value(key: str, default: Any = None) -> Any:
    config = load_runtime_config()
    return config.get(key, default)
