import os
import random
import time

from fastapi import FastAPI, HTTPException, Request
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)
from starlette.responses import Response

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# ------------------------------------------------------------------
# OpenTelemetry Configuration
# ------------------------------------------------------------------

OTLP_ENDPOINT = os.getenv(
    "OTEL_EXPORTER_OTLP_ENDPOINT",
    "http://otel-collector:4317",
)

resource = Resource.create(
    {
        "service.name": "checkout-api",
        "service.version": "1.0.0",
    }
)

provider = TracerProvider(resource=resource)
provider.add_span_processor(
    BatchSpanProcessor(
        OTLPSpanExporter(
            endpoint=OTLP_ENDPOINT,
            insecure=True,
        )
    )
)

trace.set_tracer_provider(provider)

# ------------------------------------------------------------------
# FastAPI App
# ------------------------------------------------------------------

app = FastAPI(
    title="Checkout API",
    version="1.0.0",
)

# ------------------------------------------------------------------
# Prometheus Metrics
# ------------------------------------------------------------------

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["endpoint"],
)

checkout_processing_duration_seconds = Histogram(
    "checkout_processing_duration_seconds",
    "Checkout processing latency",
)

# ------------------------------------------------------------------
# Middleware
# ------------------------------------------------------------------

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    endpoint = request.url.path

    start_time = time.time()

    try:
        response = await call_next(request)
        status = str(response.status_code)

    except Exception:
        duration = time.time() - start_time

        http_request_duration_seconds.labels(
            endpoint=endpoint
        ).observe(duration)

        http_requests_total.labels(
            endpoint=endpoint,
            status="500",
        ).inc()

        raise

    duration = time.time() - start_time

    http_request_duration_seconds.labels(
        endpoint=endpoint
    ).observe(duration)

    http_requests_total.labels(
        endpoint=endpoint,
        status=status,
    ).inc()

    return response

# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------

@app.get("/healthz")
async def healthz():
    return {
        "status": "ok",
        "service": "checkout-api",
    }


@app.post("/checkout")
async def checkout():
    start = time.time()

    # Simulate processing latency
    sleep_time = random.uniform(0.2, 2.5)
    time.sleep(sleep_time)

    # Simulate intermittent failures (~10%)
    if random.random() < 0.8:
        checkout_processing_duration_seconds.observe(
            time.time() - start
        )
        raise HTTPException(
            status_code=500,
            detail="Checkout processing failed",
        )

    checkout_processing_duration_seconds.observe(
        time.time() - start
    )

    return {
        "status": "success",
        "transaction_id": random.randint(
            100000,
            999999,
        ),
        "processing_time_seconds": round(
            sleep_time,
            3,
        ),
    }


@app.get("/metrics")
async def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )