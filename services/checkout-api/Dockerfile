# -----------------------------
# Builder
# -----------------------------
  FROM python:3.12-slim AS builder

  WORKDIR /build
  
  COPY requirements.txt .
  
  RUN pip install --no-cache-dir --upgrade pip && \
      pip install --prefix=/install --no-cache-dir -r requirements.txt
  
  # -----------------------------
  # Runtime
  # -----------------------------
  FROM python:3.12-slim
  
  WORKDIR /app
  
  COPY --from=builder /install /usr/local
  COPY app.py .
  
  EXPOSE 8000
  
  ENV PYTHONUNBUFFERED=1
  ENV OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
  
  CMD ["opentelemetry-instrument", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]