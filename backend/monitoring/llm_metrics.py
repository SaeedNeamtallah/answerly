"""
LLM Usage Monitoring (Gemini / LLM providers)
Prometheus metrics for production-level tracking
"""

import logging
import time
from prometheus_client import Counter, Histogram, Gauge

logger = logging.getLogger(__name__)

# ------------------------
# Metrics
# ------------------------

LLM_REQUEST_COUNT = Counter(
    "llm_request_count",
    "Total LLM requests",
    ["model", "status"]
)

LLM_LATENCY = Histogram(
    "llm_latency_seconds",
    "LLM response time",
    ["model"]
)

LLM_TOKENS = Counter(
    "llm_tokens_total",
    "Total tokens used",
    ["model", "type"]  # input / output
)

LLM_COST = Counter(
    "llm_cost_total_usd",
    "Estimated LLM cost in USD",
    ["model"]
)

LLM_ERRORS = Counter(
    "llm_errors_total",
    "Total LLM errors",
    ["model"]
)

# ------------------------
# Tracker Helper
# ------------------------

class LLMTracker:

    def __init__(self, model: str):
        self.model = model
        self.start_time = None

    def start(self):
        self.start_time = time.time()

    def success(self, input_tokens=0, output_tokens=0, cost=0.0):
        latency = time.time() - self.start_time

        LLM_REQUEST_COUNT.labels(model=self.model, status="success").inc()
        LLM_LATENCY.labels(model=self.model).observe(latency)

        if input_tokens:
            LLM_TOKENS.labels(model=self.model, type="input").inc(input_tokens)

        if output_tokens:
            LLM_TOKENS.labels(model=self.model, type="output").inc(output_tokens)

        if cost:
            LLM_COST.labels(model=self.model).inc(cost)

    def error(self):
        LLM_REQUEST_COUNT.labels(model=self.model, status="error").inc()
        LLM_ERRORS.labels(model=self.model).inc()