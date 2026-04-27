import time
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import FastAPI

# ===== القياسات =====

REQUEST_COUNT = Counter(
    name="http_requests_total",
    documentation="Total number of HTTP requests",
    labelnames=["method", "endpoint", "status_code"]
)

REQUEST_DURATION = Histogram(
    name="http_request_duration_seconds",
    documentation="HTTP request duration in seconds",
    labelnames=["method", "endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

# ===== الـ Middleware =====

class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time

        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=str(response.status_code)
        ).inc()

        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)

        return response


# ===== الـ /metrics endpoint =====

def add_metrics_endpoint(app: FastAPI):
    @app.get("/metrics", include_in_schema=False)
    async def metrics():
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )