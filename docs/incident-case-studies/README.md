# Incident Case Studies — Athena Platform

This directory documents five deliberately-simulated production incidents on the
Athena observability platform. Each scenario was injected intentionally to
validate detection, alerting, and root-cause-analysis workflows across the
metrics, logs, and traces pillars.

Each case study follows a structured incident-review format:
**Situation → Detection → Investigation → Root Cause → Resolution → Prevention.**

| # | Incident | Primary Signal | Pillar Exercised |
|---|----------|----------------|------------------|
| 01 | [Memory leak → OOMKilled](./01-memory-leak.md) | Pod restarts, memory saturation | Metrics + Logs |
| 02 | [Latency injection → SLO breach](./02-latency-injection.md) | p99 latency, burn-rate alert | Metrics + Traces |
| 03 | [Dependency failure → cascading errors](./03-dependency-failure.md) | Error rate, trace gaps | Traces + Metrics |
| 04 | [Error spike → fast-burn alert](./04-error-spike.md) | 5xx rate, error budget | Metrics + Logs |
| 05 | [Readiness probe misconfig → traffic loss](./05-probe-misconfig.md) | Endpoint availability | Kubernetes + Metrics |

## Why simulate failures?

> "Hope is not a strategy." — Google SRE

Building dashboards and alerts is only half of observability. The other half is
proving they actually *work* when something breaks. These exercises validated
that the Athena alerting pipeline detects real failures, that dashboards surface
the right signal, and that metric/log/trace correlation enables fast RCA.

Each incident below took the platform from "looks healthy" to "actively broken"
and back, with the full investigation trail documented.
