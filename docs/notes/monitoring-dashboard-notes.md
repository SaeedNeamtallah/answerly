# Monitoring Dashboard Notes

## Docker Desktop and WSL node-exporter noise

The bundled Node Exporter Full dashboard is useful for local infrastructure checks, but on Windows Docker Desktop and WSL it can report many virtual filesystems and bind mounts. Mountpoints under paths such as `/mnt/host/`, `/mnt/wsl/`, `/mnt/docker-desktop`, `/run/desktop/`, and `/parent-distro/` may produce noisy disk panels or `N/A` values. Treat those as local runtime artifacts unless the same issue appears on the real Linux host filesystem.

## Expected `N/A` panels

Replication lag can be `N/A` in the PostgreSQL dashboard when the local stack is not configured for replication. Query-runtime panels depend on `pg_stat_statements` metrics being available from postgres-exporter; they should be treated as optional if those metrics are missing in another environment.

## Celery, Redis, and RabbitMQ

Celery task/document metrics are currently scraped from the worker metrics endpoint at `worker:9108/metrics`, exposed on the host as `127.0.0.1:9108`. The Celery duration panels are valid when recent task samples exist.

Redis and RabbitMQ are part of the runtime path, but this repo does not currently provision dedicated Redis or RabbitMQ exporters. Add those exporters before creating first-class Redis or RabbitMQ dashboards.

## Qdrant

Prometheus scrapes Qdrant at `qdrant:6333/metrics`. The local dashboard uses Qdrant health and collection/vector metrics that are available from the built-in exporter. Search-latency metrics may stay at zero or empty until Qdrant emits search samples.
