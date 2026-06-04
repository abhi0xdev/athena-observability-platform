# Athena — Architecture & Design Rationale

This document explains **what** the platform does, **how** the pieces fit, and
crucially **why** each technology was chosen over its alternatives. It's written
to be the reasoning a reviewer would want to see — not just a component list.

---

## 1. Design Goals

Athena was built to satisfy five goals, in priority order:

1. **Demonstrate all three observability pillars** — metrics, logs, traces — and
   how they correlate, not in isolation.
2. **Be realistic** — polyglot services, real instrumentation libraries, real
   failure modes — not a toy single-service demo.
3. **Use the modern open-source stack** companies actually run in 2025–2026.
4. **Implement SLO-based alerting properly** — burn-rate alerts, not naive
   threshold alerts.
5. **Prove the platform works** by breaking it deliberately and documenting the
   investigations.

---

## 2. The Three Pillars & Data Flow

### Metrics flow

#### Service exposes /metrics  →  Prometheus scrapes (pull, 15s)  →  TSDB  →  Grafana / Alertmanager

Each service exposes a `/metrics` endpoint using a Prometheus client library.
Prometheus discovers them through `ServiceMonitor` CRDs (the Prometheus Operator
pattern) and scrapes every 15 seconds. Metrics power dashboards and alerts.

### Logs flow

#### Container stdout  →  Promtail (DaemonSet)  →  Loki  →  Grafana

Promtail runs as a DaemonSet on every node, tails container stdout, attaches
Kubernetes metadata labels (namespace, pod, container), and ships to Loki. Loki
indexes only those labels, not log content.

### Traces flow

#### Service (OTel SDK)  →  OTLP  →  OTel Collector  →  Tempo  →  Grafana

Services are instrumented with OpenTelemetry SDKs and export spans over OTLP to
a central OpenTelemetry Collector, which batches and forwards to Tempo. Tempo
stores traces for retrieval by trace ID and TraceQL.

### Correlation
All three backends are Grafana data sources, enabling the core observability
workflow: **notice an anomaly in a metric → open the relevant trace → drill into
the logs for that exact request** — without leaving Grafana.

---

## 3. Technology Choices & Trade-offs

> This section is the heart of the document — the "why" behind every pick.

### Why Prometheus for metrics
**Chosen because:** the pull model gives a free up/down signal (the `up` metric),
PromQL is the de-facto query standard, and the exporter ecosystem covers every
layer of infrastructure.
**Trade-off:** pull doesn't natively suit short-lived batch jobs (they may die
before being scraped) — the Pushgateway exists for that narrow case.
**Alternatives considered:** InfluxDB (push-based, weaker ecosystem),
VictoriaMetrics / Mimir (Prometheus-compatible, for larger scale than this
project needs).

### Why Loki for logs (vs ELK/Elasticsearch)
**Chosen because:** Loki indexes only metadata labels, not full log content.
The design assumption — that you query logs by *context* (which service, which
pod) that you already know from a dashboard or trace — holds for most
operational use. Result: ~10× cheaper storage and far lower operational burden
than Elasticsearch.
**Trade-off:** no fast full-text search across arbitrary log content; LogQL
filtering scans rather than indexes content.
**When ELK still wins:** heavy ad-hoc full-text search, complex log analytics,
security/SIEM use cases.

### Why Tempo for traces (vs Jaeger)
**Chosen because:** Tempo applies Loki's philosophy to traces — store cheaply,
retrieve by ID, no expensive attribute indexing. Integrates natively with
Grafana and accepts OTLP directly.
**Trade-off:** less rich free-form span search than fully-indexed Jaeger
(mitigated by TraceQL and exemplar links from metrics).
**Alternatives considered:** Jaeger (indexes everything — more flexible, more
costly), vendor APM (Datadog, Dynatrace — managed but paid and lock-in-prone).

### Why OpenTelemetry for instrumentation (vs vendor SDKs)
**Chosen because:** OTel decouples instrumentation from backend. Instrument once
with vendor-neutral SDKs; swap the backend (Tempo → Datadog → Honeycomb) without
touching application code. This is the industry direction — every major vendor
now ingests OTLP.
**Trade-off:** OTel SDKs and the collector add a moving part and a learning
curve vs a single-vendor agent.

### Why kube-prometheus-stack (Helm) for deployment
**Chosen because:** it bundles Prometheus Operator, Grafana, Alertmanager,
node-exporter, and kube-state-metrics with sane defaults and CRD-based config
(`ServiceMonitor`, `PrometheusRule`) — the same pattern used in production.
**Trade-off:** large and opinionated; for a minimal setup, raw manifests would
be lighter.

### Why kind for the cluster (vs minikube / cloud)
**Chosen because:** kind runs a real multi-node Kubernetes inside Docker — fast,
free, disposable, and close enough to production behavior for this purpose.
**Trade-off:** no real cloud load balancers or managed control plane; uses
NodePort + port-mapping instead of cloud ingress.

---

## 4. SLO & Alerting Design

### The SLI
Availability for `checkout-api`, defined as the proportion of non-5xx requests:

sum(rate(http_requests_total{status!~"5.."}[window])) / sum(rate(http_requests_total[window]))

### The SLO
**99.5% availability over a 30-day rolling window** → an error budget of 0.5%,
roughly 216 minutes per month.

### Why multi-window, multi-burn-rate alerting
A naive alert ("fire if error rate > 1%") flaps on transient blips and doesn't
reflect actual budget risk. Following the Google SRE Workbook, Athena uses
**burn rate** — how fast the error budget is being consumed relative to the SLO:

- **Fast burn:** budget burning at 14.4× → would exhaust the monthly budget in
  ~2 days. Requires a short *and* a longer window to both confirm before firing
  (cuts false positives). Severity: critical / page.
- **Slow burn:** budget burning at ~6× over hours → a creeping degradation.
  Severity: warning.

The dual-window requirement (e.g., 5m **and** 1h both breaching) means a
momentary spike doesn't page anyone, but a sustained problem does — quickly.

### Routing
Alertmanager routes by severity: critical → pager-style receiver, warning →
lower-urgency receiver, with grouping and inhibition to prevent alert storms
(e.g., a dependency-down alert inhibits the downstream symptom alerts).

---

## 5. Failure-Mode Validation

A platform that's never tested against failure is unproven. Five scenarios were
injected (full write-ups in `docs/incident-case-studies/`):

| Scenario | Validates |
|---|---|
| Memory leak → OOMKilled | Memory metrics + restart alerting catch leaks |
| Latency injection | Burn-rate alert detects latency-SLO breach; traces localize cause |
| Dependency failure | `up==0` root-cause alert + trace gaps reveal cascade origin |
| Error spike | Fast-burn SLO alert fires end to end through to webhook |
| Probe misconfig | Endpoint-count signal catches silent traffic loss |

Each confirmed that detection, alerting, and metric/log/trace correlation
function as designed.

---

## 6. What I'd Do Differently at Production Scale

Honest limitations of this project and how they'd change in a real environment:

- **Storage:** local filesystem / PVCs here; production would use object storage
  (S3/GCS/Azure Blob) behind Loki, Tempo, and Mimir for durability and scale.
- **High availability:** single replicas of Prometheus/Loki/Tempo here;
  production needs HA pairs or horizontally-sharded variants (Mimir, Thanos).
- **Long-term metrics:** 15-day local retention here; production would add Thanos
  or Mimir for months/years of downsampled history.
- **Cardinality control:** at scale, label cardinality is the #1 cost/perf risk;
  I'd add relabeling rules and cardinality monitoring.
- **Security:** mTLS between components, RBAC-scoped scrape configs, and secret
  management (Vault / sealed-secrets) for webhook credentials.
- **GitOps:** here applied via Helm + kubectl; production would manage all of
  this declaratively through ArgoCD with Git as the source of truth.

---

## 7. Key Takeaways

1. **Observability is three correlated pillars, not three separate tools** — the
   value is in jumping between metric, trace, and log for one request.
2. **The pull model's free up/down signal** is foundational to reliability work.
3. **Index metadata, not content** (Loki/Tempo) is the modern cost-efficient
   pattern.
4. **OpenTelemetry ends vendor lock-in** by decoupling instrumentation from backend.
5. **Burn-rate alerting** aligns paging with real SLO risk, not arbitrary
   thresholds — the single biggest upgrade over naive alerting.
