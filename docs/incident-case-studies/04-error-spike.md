# Incident 04 — Error Rate Spike Triggering Fast-Burn Alert

**Date simulated:** [DATE]
**Service affected:** checkout-api (Python / FastAPI)
**Severity:** P1 (active error budget burn)
**Detection method:** Multi-window multi-burn-rate SLO alert
**Time to detect:** ~[X] minutes (alert fired automatically)

---

## Situation

`checkout-api` was modified to return HTTP 500 for a percentage of requests,
simulating a bad deployment — a code regression, a misconfiguration, or a failed
downstream write. This is the scenario the error-budget SLO and fast-burn alert
were specifically designed to catch, so this incident doubles as a validation of
the alerting design from Day 8.

## How the failure was injected

```python
import random

@app.post("/checkout")
async def checkout(payload: dict):
    if random.random() < 0.3:        # 30% error injection
        raise HTTPException(status_code=500, detail="Simulated downstream failure")
    return {"status": "ok", "orderId": generate_id()}
```

Traffic generated:
```bash
for i in {1..600}; do curl -s -X POST http://localhost:8001/checkout > /dev/null; done
```

## Detection

Detected automatically by the **fast-burn SLO alert** (the headline result of
this exercise):

1. The availability SLI dropped sharply:
```promql
   sum(rate(http_requests_total{app="checkout-api",status!~"5.."}[5m]))
     / sum(rate(http_requests_total{app="checkout-api"}[5m]))
```
   Fell from ~1.0 to ~0.7 (30% error rate).

2. The **fast-burn alert** fired within minutes. The multi-window condition
   (short window confirming AND longer window confirming) was satisfied, meaning
   the 30-day error budget was being consumed at a dangerously high rate.

3. The alert routed through Alertmanager to the configured webhook receiver.

📸 Screenshot: `docs/screenshots/incident-04-error-rate.png`
📸 Screenshot: `docs/screenshots/incident-04-burn-alert.png`
📸 Screenshot: `docs/screenshots/incident-04-webhook-received.png`

## Investigation

1. **Quantified the error rate** — ~30% of checkout requests returning 5xx.

2. **Identified the error signature in logs:**
```logql
   {app="checkout-api"} | json | status="500"
```
   All errors showed the same message: "Simulated downstream failure" — a
   uniform error signature pointing to a single code path, not scattered
   transient failures.

3. **Confirmed timing aligned with the deployment** — the error onset matched
   the rollout of the modified version, the strongest signal of a bad deploy.

## Root Cause

A code change introduced a 30% failure rate on the `/checkout` endpoint. In a
real incident, the immediate mitigation for a bad deploy is to **roll back**
rather than debug forward.

## Resolution

The error-injecting code was reverted and redeployed (the real-world equivalent
of `kubectl rollout undo`). The availability SLI returned to ~1.0 and the
burn-rate alert auto-resolved.

## Prevention

- **Multi-window burn-rate alerting** (validated here) — distinguishes a real
  sustained error budget threat from a transient blip.
- **Deployment correlation:** annotate Grafana with deployment events so error
  onset visually aligns with releases — making "is this a bad deploy?" instant.
- **Progressive delivery:** canary or blue-green rollouts would expose only a
  fraction of traffic to a bad version, containing blast radius.
- **Automated rollback:** wire the deployment pipeline to auto-rollback if the
  error SLI breaches threshold within N minutes of a release.

## Reflection

This was the cleanest validation of the Day 8 alerting work: a real error
condition produced a fast-burn page end-to-end, through Prometheus →
Alertmanager → webhook. The uniform error signature in logs immediately
distinguished a systemic code issue from random transient failures. The biggest
operational takeaway: for a bad deploy, *roll back first, investigate second* —
the error budget is burning while you debug.
