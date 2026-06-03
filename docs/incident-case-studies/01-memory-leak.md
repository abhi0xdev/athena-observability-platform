# Incident 01 — Memory Leak Leading to OOMKilled Pods

**Date simulated:** [DATE]
**Service affected:** checkout-api (Python / FastAPI)
**Severity:** P2 (degraded, no full outage due to replicas)
**Detection method:** Prometheus memory metrics + Kubernetes restart count
**Time to detect:** ~[X] minutes
**Time to root cause:** ~[X] minutes

---

## Situation

The `checkout-api` service exposes an endpoint that, due to a simulated bug,
appends request data to an in-memory list that is never cleared — an unbounded
cache. Under sustained traffic, the pod's memory usage climbs steadily until it
hits the configured memory limit (512Mi), at which point the kernel OOMKills the
container. Kubernetes restarts the pod, and the cycle repeats.

This mirrors one of the most common real-world reliability issues: a slow memory
leak that doesn't cause immediate downtime (because replicas absorb it) but
produces a sawtooth memory pattern, periodic restarts, and intermittent latency
spikes during each restart.

## How the failure was injected

A `/leak` endpoint was added to checkout-api:

```python
LEAKY_CACHE = []   # never cleared — simulates an unbounded cache

@app.post("/leak")
async def leak(payload: dict):
    LEAKY_CACHE.append("x" * 100_000)   # ~100KB per call
    return {"cache_size": len(LEAKY_CACHE)}
```

Traffic was generated:

```bash
for i in {1..2000}; do curl -s -X POST http://localhost:8001/leak \
  -H "Content-Type: application/json" -d '{}' > /dev/null; done
```

## Detection

The issue surfaced through two signals simultaneously:

1. **Memory saturation dashboard** (golden signals) showed `checkout-api`
   container memory climbing on a steady linear slope — from a ~80Mi baseline
   toward the 512Mi limit — rather than a traffic-correlated spike.

   PromQL used:
```promql
   container_memory_working_set_bytes{pod=~"checkout-api.*"}
```

2. **Pod restart count** began incrementing:
```promql
   kube_pod_container_status_restarts_total{pod=~"checkout-api.*"}
```

📸 Screenshot: `docs/screenshots/incident-01-memory-sawtooth.png`

## Investigation

The investigation followed a deliberate narrowing process:

1. **Confirmed the pattern was a leak, not load.** The memory slope was constant
   regardless of request rate — a load-driven issue would track the traffic
   curve. A constant climb regardless of traffic points to accumulation.

2. **Confirmed OOMKilled as the restart cause.** Checked the pod's last state:
```bash
   kubectl describe pod <checkout-api-pod> | grep -A5 "Last State"
   # Last State: Terminated
   #   Reason: OOMKilled
   #   Exit Code: 137
```
   Exit code 137 = 128 + 9 (SIGKILL), the signature of an OOM kill.

3. **Correlated to a specific endpoint via logs.** Queried Loki for request
   patterns during the growth window:
```logql
   {app="checkout-api"} | json | endpoint="/leak"
```
   The `/leak` endpoint was being called repeatedly, immediately preceding the
   memory growth.

## Root Cause

An unbounded in-memory list (`LEAKY_CACHE`) accumulated ~100KB per request and
was never evicted. Under sustained traffic the process exceeded its 512Mi memory
limit, triggering the kernel OOM killer (exit 137), which Kubernetes interpreted
as a container crash and restarted.

## Resolution

In a real scenario the fix would be a code change — bound the cache (LRU with a
max size, or a TTL-based eviction). For the simulation, the leaky endpoint was
removed and the pod redeployed. Memory immediately stabilized at the ~80Mi
baseline with a flat line.

## Prevention

- **Memory limit alerting:** added an alert when working-set memory exceeds 80%
  of the limit for a sustained period — catches leaks *before* the OOMKill.
```promql
  container_memory_working_set_bytes{pod=~"checkout-api.*"}
    / on(pod) kube_pod_container_resource_limits{resource="memory"} > 0.8
```
- **Restart-count alerting:** alert when restart count increases more than N
  times in an hour — catches crash loops early.
- **Code review practice:** unbounded in-memory caches should always have a
  max-size or TTL. This is a reviewable pattern.

## Reflection

The key learning was the *diagnostic hierarchy*: a steady memory climb that
ignores traffic is almost always a leak, and exit code 137 immediately confirms
OOM. Combining the metric (memory slope) with the log correlation (which endpoint
drove it) cut the time-to-root-cause dramatically. Detecting at 80% of limit
rather than waiting for the OOMKill would convert this from a P2 with restarts
into a non-event.
