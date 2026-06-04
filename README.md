# 🔭 Athena — End-to-End Observability Platform

> A self-built, production-grade observability platform demonstrating the modern
> SRE telemetry stack — **metrics, logs, and traces** — wired together from
> scratch on Kubernetes, with SLO-based alerting and five documented incident
> investigations.

![status](https://img.shields.io/badge/status-complete-success)
![k8s](https://img.shields.io/badge/Kubernetes-kind-blue)
![stack](https://img.shields.io/badge/stack-LGTM%20%2B%20OpenTelemetry-orange)

**Author:** [Abhinandan Gayaki](https://linkedin.com/in/abhinandan-gayaki) ·
[GitHub](https://github.com/abhi0xdev) ·
[Email](mailto:abhinandangayaki@gmail.com)

---

## 📌 What This Is & Why I Built It

After 4 years operating production observability tooling (Prometheus, Grafana,
Dynatrace, Azure Application Insights) at Cognizant, I wanted to move from
*operating* an observability stack someone else built to *building one end to
end* myself.

**Athena** instruments three polyglot microservices, pipes their telemetry
through a complete open-source observability stack, defines real SLIs/SLOs with
multi-window burn-rate alerting, and includes **five deliberately-injected
production incidents** — each documented as a full root-cause investigation.

The goal: bridge the gap between *"I've used observability tools"* and *"I've
designed and debugged an observability platform."*

---

## 🏛 Architecture (high level)

<img width="1472" height="1764" alt="image" src="https://github.com/user-attachments/assets/a202be88-f910-4b4b-aac4-1ba500c2f154" />

Three telemetry pillars feed three purpose-built backends, unified in Grafana.
Failures simulated at the service layer propagate naturally through metrics,
logs, and traces — letting me practice end-to-end RCA flow.

Full design rationale, trade-offs, and data flow in **[ARCHITECTURE.md](./ARCHITECTURE.md)**.

---

## 🧰 Tech Stack

| Layer | Tooling | Why |
|---|---|---|
| Orchestration | Kubernetes (`kind`, 3 nodes) | Local multi-node cluster |
| Packaging | Helm | Repeatable chart installs |
| Sample apps | Python (FastAPI), Node.js (Express), Go | Polyglot, realistic |
| Instrumentation | Prometheus client libs + OpenTelemetry SDKs | Cross-language telemetry |
| Metrics | Prometheus, kube-state-metrics, node-exporter | Pull-based time series |
| Logs | Loki + Promtail | Label-indexed, cost-efficient |
| Traces | Tempo + OpenTelemetry Collector | Distributed tracing |
| Visualization | Grafana | Single pane: metrics + logs + traces |
| Alerting | Alertmanager | Multi-window burn-rate SLO alerts |

---

## ✅ What Was Built

- **Polyglot instrumentation** — three services in Python, Node.js, and Go, each
  emitting Prometheus metrics, structured logs, and OpenTelemetry traces
- **Full LGTM stack** — Loki (logs), Grafana (viz), Tempo (traces),
  Prometheus (metrics) deployed via Helm
- **Auto-discovery** — Prometheus scrapes services via `ServiceMonitor` CRDs
- **Three dashboards** — RED method (per-service), golden signals (cluster),
  and an SLI/error-budget dashboard
- **SLO-based alerting** — multi-window, multi-burn-rate error-budget alerts
  following the [Google SRE Workbook](https://sre.google/workbook/alerting-on-slos/)
- **Cross-signal correlation** — jump from a metric anomaly → trace → log line in Grafana
- **Five incident investigations** — see below

---

## 🚨 Incident Case Studies

Five failures were deliberately injected and investigated end to end. Each is a
full RCA write-up in [`docs/incident-case-studies/`](./docs/incident-case-studies/):

| # | Incident | Signal | What it demonstrates |
|---|----------|--------|----------------------|
| 01 | [Memory leak → OOMKilled](docs/incident-case-studies/01-memory-leak.md) | Memory saturation, restarts | Leak vs load diagnosis, exit 137 |
| 02 | [Latency injection → SLO breach](docs/incident-case-studies/02-latency-injection.md) | p99 latency, burn-rate alert | Metrics + traces for latency |
| 03 | [Dependency failure → cascade](docs/incident-case-studies/03-dependency-failure.md) | Error rate, trace gaps | Root vs symptom in microservices |
| 04 | [Error spike → fast-burn alert](docs/incident-case-studies/04-error-spike.md) | 5xx rate, error budget | SLO alerting, bad-deploy response |
| 05 | [Probe misconfig → traffic loss](docs/incident-case-studies/05-probe-misconfig.md) | Endpoint availability | Readiness vs liveness, Service routing |

---

## 🚀 Run It Locally

### Prerequisites
- Docker Desktop or Rancher Desktop · `kind` v0.20+ · `kubectl` v1.28+ · `helm` v3.12+
- ~8 GB RAM, ~30 GB free disk

### Bring it up
```bash
git clone https://github.com/abhi0xdev/athena-observability-platform.git
cd athena-observability-platform
./scripts/setup.sh        # creates cluster, installs stack, deploys services
```

### Access the UIs

```bash
# Grafana   → http://localhost:3030  (admin / prom-operator)
# Prometheus→ http://localhost:9090
# Alertmanager → http://localhost:9093
```

### Tear down

```bash
./scripts/teardown.sh
```

---

## 📁 Repository Structure

athena-observability-platform/
├── README.md                  ← this file
├── ARCHITECTURE.md            ← design rationale & trade-offs
├── infra/                     ← kind cluster config
├── services/                  ← checkout-api, orders-service, payments-worker
├── k8s/                       ← Deployment + Service manifests
├── observability/             ← Prometheus, Grafana, Loki, Tempo, OTel, Alertmanager configs
├── docs/
│   ├── day-by-day-log.md      ← build notes, debugging journeys
│   ├── slo-design.md          ← SLI/SLO rationale
│   ├── incident-case-studies/ ← 5 RCA write-ups
│   └── screenshots/           ← dashboards, traces, alerts
└── scripts/                   ← setup.sh / teardown.sh

---

## Screenshots 

<img width="1037" height="450" alt="image (6)" src="https://github.com/user-attachments/assets/5eab5340-ab61-49cb-a787-522237f6af63" />

---

<img width="1914" height="852" alt="image (7)" src="https://github.com/user-attachments/assets/c799e67a-ca49-42af-b5b2-cb8099964321" />

---

<img width="1885" height="847" alt="image (8)" src="https://github.com/user-attachments/assets/a701b2bd-8c9e-4225-8264-84a3397838af" />

---

<img width="1919" height="876" alt="image (9)" src="https://github.com/user-attachments/assets/94b70b91-0dcd-42c6-9dbb-64e1c9603706" />

---

<img width="1919" height="877" alt="image (10)" src="https://github.com/user-attachments/assets/781f5455-03a1-4610-82db-fabd922cd962" />

---

<img width="1851" height="818" alt="image (12)" src="https://github.com/user-attachments/assets/30f1b64c-7bc6-43c6-9e18-97b1898dd6b8" />


---

## 📚 References

- [Google SRE Workbook — Alerting on SLOs](https://sre.google/workbook/alerting-on-slos/)
- [The RED Method (Tom Wilkie)](https://grafana.com/blog/2018/08/02/the-red-method-how-to-instrument-your-services/)
- [The USE Method (Brendan Gregg)](http://www.brendangregg.com/usemethod.html)
- [OpenTelemetry Docs](https://opentelemetry.io/docs/) · [Grafana LGTM Stack](https://grafana.com/oss/)

---

*Built as a structured, in-public SRE/observability deep-dive. Feedback welcome.*
