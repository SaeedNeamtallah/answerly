"""
Runtime configuration storage.
Stores provider selections in a JSON file without requiring an app restart.
"""
from __future__ import annotations

from typing import Any, Dict
import json
import logging
import os
import time
from pathlib import Path

from backend.shared_config_paths import get_app_config_path

logger = logging.getLogger(__name__)


_cache: Dict[str, Any] = {}
_cache_ts: float = 0.0
_CACHE_TTL: float = 2.0  # seconds


def _load_runtime_config_from_disk(config_path: Path) -> Dict[str, Any]:
    if not config_path.exists():
        return {}
    try:
        with config_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _lock_file_path(config_path: Path) -> Path:
    return config_path.with_suffix(config_path.suffix + ".lock")


def _acquire_lock(lock_path: Path, *, timeout_seconds: float = 5.0) -> None:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + max(0.1, float(timeout_seconds))
    while True:
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            try:
                os.write(fd, str(os.getpid()).encode("utf-8", errors="ignore"))
            finally:
                os.close(fd)
            return
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise TimeoutError(f"Timed out waiting for runtime config lock: {lock_path}")
            time.sleep(0.05)


def _release_lock(lock_path: Path) -> None:
    try:
        lock_path.unlink(missing_ok=True)
    except Exception:
        logger.exception("Failed to release runtime config lock: %s", str(lock_path))


def _atomic_write_json(config_path: Path, data: dict[str, Any]) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = config_path.with_suffix(config_path.suffix + ".tmp")

    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())

    os.replace(tmp_path, config_path)


def load_runtime_config() -> Dict[str, Any]:
    global _cache, _cache_ts
    config_path = get_app_config_path()
    now = time.monotonic()
    if _cache and (now - _cache_ts) < _CACHE_TTL:
        return _cache
    if not config_path.exists():
        _cache, _cache_ts = {}, now
        return _cache
    _cache = _load_runtime_config_from_disk(config_path)
    _cache_ts = now
    return _cache


def save_runtime_config(config: Dict[str, Any]) -> None:
    global _cache, _cache_ts
    config_path = get_app_config_path()
    lock_path = _lock_file_path(config_path)
    try:
        _acquire_lock(lock_path)
        _atomic_write_json(config_path, dict(config))
    except Exception as exc:
        logger.exception("Runtime config write failed: %s", str(exc))
        raise RuntimeError("Runtime config write failed") from exc
    finally:
        _release_lock(lock_path)

    _cache = dict(config)
    _cache_ts = time.monotonic()


def update_runtime_config(updates: Dict[str, Any]) -> Dict[str, Any]:
    config_path = get_app_config_path()
    lock_path = _lock_file_path(config_path)
    try:
        _acquire_lock(lock_path)
        current = _load_runtime_config_from_disk(config_path)
        merged = dict(current)
        merged.update(dict(updates))
        _atomic_write_json(config_path, merged)
    except Exception as exc:
        logger.exception("Runtime config write failed: %s", str(exc))
        raise RuntimeError("Runtime config write failed") from exc
    finally:
        _release_lock(lock_path)

    global _cache, _cache_ts
    _cache = dict(merged)
    _cache_ts = time.monotonic()
    return merged


def get_runtime_value(key: str, default: Any = None) -> Any:
    config = load_runtime_config()
    return config.get(key, default)
