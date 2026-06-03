# Incident 03 — Dependency Failure Causing Cascading Errors

**Date simulated:** [DATE]
**Services affected:** orders-service (caller), checkout-api (failed dependency)
**Severity:** P1 (functional failure of the order flow)
**Detection method:** Error rate spike + distributed trace gaps
**Time to detect:** ~[X] minutes

---

## Situation

`orders-service` depends on `checkout-api` to complete an order. This incident
simulates the dependency becoming unavailable — `checkout-api` was scaled to
zero replicas, mimicking a crashed or evicted downstream service. The goal was
to observe how a downstream failure surfaces as cascading errors upstream, and
how distributed tracing localizes the actual point of failure.

## How the failure was injected

```bash
# Take the dependency down
kubectl scale deployment checkout-api --replicas=0

# Generate order traffic that depends on checkout-api
for i in {1..200}; do curl -s -X POST http://localhost:8002/orders > /dev/null; done
```

## Detection

1. **orders-service error rate spiked:**
```promql
   sum(rate(http_requests_total{app="orders-service",status=~"5.."}[5m]))
     / sum(rate(http_requests_total{app="orders-service"}[5m]))
```
   Error ratio jumped from ~0 to a high percentage.

2. **checkout-api disappeared from Prometheus targets** — the `up` metric for
   checkout-api went to 0:
```promql
   up{app="checkout-api"}
```
   This is the value of the pull model: an absent target is *visibly* down, not
   just silent.

📸 Screenshot: `docs/screenshots/incident-03-error-cascade.png`

## Investigation

The critical question in any cascading failure: **where is the actual root, and
where are just the symptoms?**

1. **orders-service was erroring**, but was orders-service itself broken, or was
   it failing *because* of something downstream?

2. **Distributed traces answered it.** Opened Tempo and inspected a failing
   `/orders` trace. The trace showed:
   - orders-service span: started normally
   - the outbound call to checkout-api: **failed / no child span** — connection
     refused, because no checkout-api pods existed
   - orders-service then returned 5xx

   The trace made it unambiguous: orders-service was healthy, the failure
   originated at the checkout-api dependency.

3. **Confirmed checkout-api was down:**
```bash
   kubectl get pods -l app=checkout-api
   # No resources found — replicas scaled to 0
```

## Root Cause

The `checkout-api` dependency had zero running replicas. orders-service's
outbound calls failed with connection errors, which it surfaced as 5xx
responses to its own callers — a classic cascading failure where the *symptom*
(orders-service errors) is one hop removed from the *cause* (checkout-api down).

## Resolution

```bash
kubectl scale deployment checkout-api --replicas=2
kubectl rollout status deployment checkout-api
```

Once checkout-api pods were Ready and rejoined the Service endpoints,
orders-service error rate returned to baseline.

## Prevention

- **Dependency-aware alerting:** alert on `up == 0` for every critical service,
  so the *root* (checkout-api down) pages before the *symptom* (orders errors).
- **Alert inhibition:** configure Alertmanager so that when checkout-api is
  down, the downstream orders-service error alert is *inhibited* — on-call gets
  one root-cause page, not a storm of symptom pages.
- **Resilience patterns (app-level):** timeouts, retries with backoff, and
  circuit breakers on the orders→checkout call would degrade more gracefully
  than hard 5xx.

## Reflection

This incident demonstrated why distributed tracing is indispensable for
microservices. Metrics told me *something* was wrong with orders-service, but
only the trace showed the failure originated one hop downstream. Without tracing,
on-call might have wasted time investigating orders-service itself. The broader
lesson: in distributed systems, alert on root-cause signals (`up == 0`) and use
inhibition to suppress symptom alerts, so the page points at the real problem.
