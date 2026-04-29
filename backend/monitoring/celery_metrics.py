"""Prometheus exporter for metrics emitted inside Celery worker processes."""
from __future__ import annotations

import logging
import os
import shutil
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

from celery.signals import worker_init, worker_process_shutdown
from prometheus_client import multiprocess
from prometheus_client.mmap_dict import MmapedDict

from backend.config import settings


logger = logging.getLogger(__name__)
_SERVER_STARTED = False


def _multiproc_dir() -> Path:
    return Path(settings.celery_prometheus_multiproc_dir)


def _labels_text(labels: dict[str, str]) -> str:
    if not labels:
        return ""
    parts = []
    for key in sorted(labels):
        value = str(labels[key]).replace("\\", "\\\\").replace('"', '\\"')
        parts.append(f'{key}="{value}"')
    return "{" + ",".join(parts) + "}"


def _read_metric_rows(metrics_dir: Path) -> list[tuple[str, str, dict[str, str], str, float]]:
    rows: list[tuple[str, str, dict[str, str], str, float]] = []
    for db_file in metrics_dir.glob("*.db"):
        metric_type = db_file.name.split("_", 1)[0]
        try:
            mmap_dict = MmapedDict(str(db_file), read_mode=True)
            values = list(mmap_dict.read_all_values())
        except Exception:
            logger.exception("Failed to read Celery metric file %s", db_file)
            continue
        for key, value, _timestamp in values:
            metric_name, sample_name, labels, help_text = json.loads(key)
            rows.append((metric_name, sample_name, labels, help_text, float(value)))
    return rows


def _render_metrics(metrics_dir: Path) -> bytes:
    rows = _read_metric_rows(metrics_dir)
    lines: list[str] = []

    counters: dict[str, tuple[str, list[tuple[str, dict[str, str], float]]]] = {}
    histograms: dict[str, tuple[str, dict[tuple[tuple[str, str], ...], dict[str, object]]]] = {}

    for metric_name, sample_name, labels, help_text, value in rows:
        if sample_name.endswith("_total"):
            counters.setdefault(metric_name, (help_text, []))[1].append((sample_name, labels, value))
            continue

        if "_bucket" in sample_name or sample_name.endswith("_sum"):
            help_entry = histograms.setdefault(metric_name, (help_text, {}))
            grouped = help_entry[1]
            base_labels = dict(labels)
            le = base_labels.pop("le", None)
            group_key = tuple(sorted(base_labels.items()))
            group = grouped.setdefault(group_key, {"labels": base_labels, "buckets": {}, "sum": 0.0})
            if sample_name.endswith("_sum"):
                group["sum"] = value
            elif le is not None:
                group["buckets"][str(le)] = value

    for metric_name in sorted(counters):
        help_text, samples = counters[metric_name]
        lines.append(f"# HELP {metric_name}_total {help_text}")
        lines.append(f"# TYPE {metric_name}_total counter")
        for sample_name, labels, value in samples:
            lines.append(f"{sample_name}{_labels_text(labels)} {value}")

    for metric_name in sorted(histograms):
        help_text, groups = histograms[metric_name]
        lines.append(f"# HELP {metric_name} {help_text}")
        lines.append(f"# TYPE {metric_name} histogram")
        for group in groups.values():
            labels = group["labels"]
            buckets = group["buckets"]
            total = 0.0
            finite_bounds = sorted(
                [bound for bound in buckets if bound != "+Inf"],
                key=lambda item: float(item),
            )
            for bound in finite_bounds:
                total += float(buckets.get(bound, 0.0))
                bucket_labels = dict(labels)
                bucket_labels["le"] = bound
                lines.append(f"{metric_name}_bucket{_labels_text(bucket_labels)} {total}")
            total += float(buckets.get("+Inf", 0.0))
            bucket_labels = dict(labels)
            bucket_labels["le"] = "+Inf"
            lines.append(f"{metric_name}_bucket{_labels_text(bucket_labels)} {total}")
            lines.append(f"{metric_name}_count{_labels_text(labels)} {total}")
            lines.append(f"{metric_name}_sum{_labels_text(labels)} {float(group['sum'])}")

    if lines:
        lines.append("")
    return "\n".join(lines).encode("utf-8")


class _MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path not in {"/metrics", "/"}:
            self.send_response(404)
            self.end_headers()
            return
        body = _render_metrics(_multiproc_dir())
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


@worker_init.connect
def start_celery_metrics_server(**_: object) -> None:
    """Start a worker-local metrics endpoint before task child processes run."""

    global _SERVER_STARTED
    if _SERVER_STARTED:
        return

    metrics_dir = _multiproc_dir()
    if metrics_dir.exists():
        shutil.rmtree(metrics_dir)
    metrics_dir.mkdir(parents=True, exist_ok=True)
    os.environ["PROMETHEUS_MULTIPROC_DIR"] = str(metrics_dir)

    server = ThreadingHTTPServer(("0.0.0.0", settings.celery_prometheus_port), _MetricsHandler)
    Thread(target=server.serve_forever, daemon=True).start()
    _SERVER_STARTED = True
    logger.info(
        "Celery Prometheus metrics endpoint listening on port %s",
        settings.celery_prometheus_port,
    )


@worker_process_shutdown.connect
def mark_worker_process_dead(pid: int | None = None, **_: object) -> None:
    """Let prometheus_client clean stale per-process metric files."""

    if pid is not None:
        multiprocess.mark_process_dead(pid)
