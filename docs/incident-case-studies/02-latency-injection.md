# Incident 02 — Latency Injection Causing SLO Breach

**Date simulated:** [DATE]
**Service affected:** orders-service (Node.js / Express)
**Severity:** P2 (latency degradation, error budget burn)
**Detection method:** p99 latency metric + multi-window burn-rate alert
**Time to detect:** ~[X] minutes (alert fired automatically)

---

## Situation

A latency regression was injected into `orders-service` — a code path that
introduces a 5–10 second artificial delay on a percentage of requests. This
simulates a common real-world failure: a slow downstream dependency, an
inefficient query, or a thread-pool exhaustion that doesn't error outright but
degrades the user experience and burns the latency SLO.

## How the failure was injected

A `/slow` code path was added that sleeps before responding:

```javascript
app.post('/orders', async (req, res) => {
  if (Math.random() < 0.4) {            // 40% of requests
    await new Promise(r => setTimeout(r, 5000 + Math.random() * 5000));
  }
  res.json({ orderId: generateId() });
});
```

Traffic generated with a steady load:
```bash
for i in {1..500}; do curl -s -X POST http://localhost:8002/orders > /dev/null & done
```

## Detection

This incident was detected **automatically by the alerting pipeline** — the
ideal outcome. The sequence:

1. **p99 latency dashboard** spiked from a ~200ms baseline to multi-second
   values:
```promql
   histogram_quantile(0.99,
     sum(rate(http_request_duration_seconds_bucket{app="orders-service"}[5m])) by (le))
```

2. **The SLO burn-rate alert fired.** The latency SLI (proportion of requests
   served under the 1s latency objective) dropped below target, and the
   fast-burn alert triggered within minutes.

📸 Screenshot: `docs/screenshots/incident-02-latency-p99.png`
📸 Screenshot: `docs/screenshots/incident-02-alert-firing.png`

## Investigation

1. **Confirmed it was latency, not errors.** Error rate stayed flat — requests
   were succeeding, just slowly. This is an important distinction: availability
   SLO was fine, latency SLO was breached.

2. **Identified the affected endpoint via traces.** Opened Tempo in Grafana and
   filtered for slow traces on orders-service. The `/orders` span showed
   multi-second durations, with the time spent *inside* the service (not in a
   downstream call) — pointing to the service's own code, not a dependency.

3. **Confirmed the proportion.** Roughly 40% of requests were slow, matching the
   injected condition.

## Root Cause

An artificial delay was introduced on ~40% of `/orders` requests. In a real
incident, the equivalent root causes would be: a slow database query, lock
contention, an undersized connection pool, or a synchronous call to a degraded
downstream service. The trace data localizing the time *within* the service span
would distinguish "our code is slow" from "a dependency is slow."

## Resolution

The injected delay was removed and the service redeployed. p99 latency returned
to the ~200ms baseline and the burn-rate alert auto-resolved (with
`send_resolved: true`, a resolution notification was delivered).

## Prevention

- **Latency SLO with burn-rate alerting** (already in place — this is what
  caught it) — alerts on *sustained* budget burn rather than instantaneous
  spikes, avoiding flapping.
- **Trace-based latency breakdown** to quickly localize whether slowness is in
  our code or a dependency.
- **Per-endpoint latency dashboards** so a regression in one endpoint isn't
  hidden by healthy aggregate latency.

## Reflection

This incident validated the single most valuable property of a good alerting
setup: it detected the problem *before a human noticed*. The multi-window
burn-rate approach meant the alert reflected real SLO risk, not a transient
blip. The trace data was decisive — it answered "is it us or a dependency?" in
seconds, which is usually the slowest question to answer in a latency incident.
