# 🔭 Athena — End-to-End Observability Platform

> A self-built, production-grade observability platform demonstrating the modern
> SRE telemetry stack — metrics, logs, and traces — wired together from scratch
> on Kubernetes.

**Status:** 🚧 Day 1 of 10 — Foundation complete, build in progress
**Author:** [Abhinandan Gayaki](https://linkedin.com/in/abhinandan-gayaki)
**Started:** [Today's Date]

---

## 📌 Why I'm Building This

After 4 years of operating production observability tooling (Prometheus, Grafana,
Dynatrace, Azure Application Insights) at Cognizant, I wanted to deepen my
hands-on skill on the *building* side of observability — not just operating
stacks set up by others.

Athena instruments three sample microservices written in different languages
and feeds their telemetry through a complete open-source LGTM stack (Loki,
Grafana, Tempo, Mimir/Prometheus), with proper SLI/SLO definitions and
multi-window burn-rate alerts. Five deliberate failure scenarios are simulated
and documented as RCA case studies.

The goal is to bridge the gap between "I've used observability tools" and "I've
built an observability platform end to end."

---

## 🏛 Architecture

<img width="1472" height="1764" alt="image" src="https://github.com/user-attachments/assets/a202be88-f910-4b4b-aac4-1ba500c2f154" />

Three telemetry pillars feed three purpose-built backends, unified in Grafana.
Failures simulated at the service layer propagate naturally through metrics,
logs, and traces — letting me practice end-to-end RCA flow.

A detailed architecture write-up is available in [`ARCHITECTURE.md`](./ARCHITECTURE.md)
(coming Day 10).

---

## 🧰 Tech Stack

| Layer | Tooling | Purpose |
|---|---|---|
| **Orchestration** | Kubernetes (via `kind`) | Local multi-node cluster |
| **Packaging** | Helm | Chart-based installs |
| **Sample apps** | Python (FastAPI), Node.js (Express), Go (net/http) | Polyglot workload |
| **Instrumentation** | Prometheus client libraries + OpenTelemetry SDKs | Cross-language telemetry |
| **Metrics** | Prometheus, kube-state-metrics, node-exporter | Time-series collection |
| **Logs** | Loki + Promtail | Label-indexed log aggregation |
| **Traces** | Tempo + OpenTelemetry Collector | Distributed tracing |
| **Visualization** | Grafana | Unified dashboards (RED, golden signals, SLI) |
| **Alerting** | Alertmanager | Multi-window burn-rate alerts on SLOs |

---

## 📅 Build Plan & Daily Progress

| Day | Focus | Status |
|---|---|---|
| **Day 1** | Cluster setup, GitHub repo, project scaffolding | ✅ **Done** |
| Day 2 | Python `checkout-api` with Prometheus metrics + OTel | 📋 Planned |
| Day 3 | Node.js `orders-service` + Go `payments-worker` | 📋 Planned |
| Day 4 | Prometheus + ServiceMonitors scraping all services | 📋 Planned |
| Day 5 | Loki + Promtail for log aggregation | 📋 Planned |
| Day 6 | OpenTelemetry Collector + Tempo for tracing | 📋 Planned |
| Day 7 | Grafana dashboards: RED, golden signals, SLI | 📋 Planned |
| Day 8 | SLI/SLO + multi-window burn-rate alerts | 📋 Planned |
| Day 9 | 5 simulated production incidents + RCA case studies | 📋 Planned |
| Day 10 | Polish, demo video, full ARCHITECTURE.md | 📋 Planned |

---

## ✅ Day 1 — What's Complete

**Goal:** Set up the local Kubernetes cluster, create the GitHub repo, and
scaffold the project structure so the rest of the build can move fast.

### What was built

- ✅ Installed prerequisites: Docker Desktop, `kind`, `kubectl`, `Helm`, `git`
- ✅ Created a 3-node `kind` cluster (1 control plane + 2 workers) with port
  mappings for Prometheus, Grafana, and a service ingress
- ✅ Created the public GitHub repository
- ✅ Scaffolded the project directory structure
- ✅ Drafted this README and the high-level architecture diagram

### Cluster setup

Cluster configuration is in [`infra/kind-config.yaml`](./infra/kind-config.yaml):

````yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: athena
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 30080
    hostPort: 8080
  - containerPort: 30090
    hostPort: 9090
  - containerPort: 30030
    hostPort: 3030
- role: worker
- role: worker
````

Created with:

````bash
kind create cluster --config infra/kind-config.yaml
````

### Verification

````bash
$ kubectl get nodes
NAME                   STATUS   ROLES           AGE   VERSION
athena-control-plane   Ready    control-plane   3m    v1.29.2
athena-worker          Ready    <none>          2m    v1.29.2
athena-worker2         Ready    <none>          2m    v1.29.2

$ kubectl get pods -n kube-system
NAME                                           READY   STATUS    RESTARTS   AGE
coredns-76f75df574-xxxxx                       1/1     Running   0          3m
coredns-76f75df574-yyyyy                       1/1     Running   0          3m
etcd-athena-control-plane                      1/1     Running   0          3m
kindnet-aaaaa                                  1/1     Running   0          3m
kube-apiserver-athena-control-plane            1/1     Running   0          3m
kube-controller-manager-athena-control-plane   1/1     Running   0          3m
kube-proxy-bbbbb                               1/1     Running   0          3m
kube-scheduler-athena-control-plane            1/1     Running   0          3m
````

📸 Screenshot: [`docs/screenshots/day-01-cluster-up.png`](./docs/screenshots/day-01-cluster-up.png)

---

## 📁 Project Structure

athena-observability-platform/
├── README.md                          ← you are here
├── ARCHITECTURE.md                    ← coming Day 10
│
├── infra/
│   └── kind-config.yaml               ← cluster config (Day 1) ✅
│
├── services/                          ← sample microservices
│   ├── checkout-api/                  ← Python (Day 2)
│   ├── orders-service/                ← Node.js (Day 3)
│   └── payments-worker/               ← Go (Day 3)
│
├── k8s/
│   ├── namespaces.yaml
│   ├── services/                      ← Deployment + Service manifests
│   └── observability/                 ← observability stack manifests
│
├── observability/                     ← observability stack configs
│   ├── prometheus/                    ← ServiceMonitors, PrometheusRules
│   ├── grafana/                       ← dashboard JSON, datasources
│   ├── loki/                          ← Loki + Promtail values
│   ├── tempo/                         ← Tempo values
│   ├── otel-collector/                ← OTel collector pipeline
│   └── alertmanager/                  ← routing config
│
├── docs/
│   ├── day-by-day-log.md              ← build notes, gotchas, fixes
│   ├── slo-design.md                  ← SLI/SLO rationale (Day 8)
│   ├── incident-case-studies/         ← RCA write-ups (Day 9)
│   │   ├── 01-memory-leak.md
│   │   ├── 02-latency-injection.md
│   │   ├── 03-dependency-failure.md
│   │   ├── 04-error-spike.md
│   │   └── 05-probe-misconfig.md
│   └── screenshots/                   ← dashboards, queries, alerts
│
└── scripts/
├── setup.sh                       ← end-to-end setup (Day 10)
└── teardown.sh

---

## 🚀 Running This Locally (current state)

> **Note:** Day 1 only sets up the cluster. The full stack will be runnable end
> to end on Day 10. Today, only the cluster bootstrap is available.

### Prerequisites

- Docker Desktop or Rancher Desktop
- [`kind`](https://kind.sigs.k8s.io/docs/user/quick-start/) v0.20+
- `kubectl` v1.28+
- `helm` v3.12+
- At least 8 GB RAM and 30 GB free disk space

### Bring up the cluster

````bash
git clone https://github.com/abhi0xdev/athena-observability-platform.git
cd athena-observability-platform

kind create cluster --config infra/kind-config.yaml

kubectl cluster-info --context kind-athena
kubectl get nodes
````

### Tear down

````bash
kind delete cluster --name athena
````

---

## 🎯 What This Project Will Demonstrate (by Day 10)

When complete, Athena will show:

* **Polyglot instrumentation** — Prometheus + OpenTelemetry across Python, Node.js, Go
* **Full LGTM stack** — Loki, Grafana, Tempo, Prometheus/Mimir wired end to end
* **Modern SRE alerting** — multi-window, multi-burn-rate error-budget alerts
  following the Google SRE Workbook chapter on alerting on SLOs
* **Cross-signal correlation** — jump from a metric anomaly to a log line to a
  distributed trace, all in Grafana
* **5 documented incident scenarios** — memory leak, latency injection,
  dependency failure, error spike, probe misconfiguration — each with a written
  RCA case study

---

## 📚 References & Inspiration

* [Google SRE Workbook — Alerting on SLOs](https://sre.google/workbook/alerting-on-slos/)
* [Grafana — The LGTM stack](https://grafana.com/oss/)
* [OpenTelemetry documentation](https://opentelemetry.io/docs/)
* [Tom Wilkie — The RED Method](https://grafana.com/blog/2018/08/02/the-red-method-how-to-instrument-your-services/)
* [Brendan Gregg — The USE Method](http://www.brendangregg.com/usemethod.html)

---

## 📬 Contact

Building this in public as part of a structured 30-day SRE/Observability prep.
Feedback, suggestions, and roasts welcome.

* **GitHub:** [@abhi0xdev](https://github.com/abhi0xdev)
* **LinkedIn:** [abhinandan-gayaki](https://linkedin.com/in/abhinandan-gayaki)
* **Email:** [abhinandangayaki@gmail.com](mailto:abhinandangayaki@gmail.com)

---

*This README is updated daily as the project progresses. Last updated: Day 1.*