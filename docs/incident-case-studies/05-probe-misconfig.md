# Incident 05 — Readiness Probe Misconfiguration Causing Traffic Loss

**Date simulated:** [DATE]
**Service affected:** payments-worker (Go)
**Severity:** P1 (service unreachable despite "running" pods)
**Detection method:** Endpoint availability + Kubernetes endpoint analysis
**Time to detect:** ~[X] minutes

---

## Situation

The `payments-worker` deployment was given a misconfigured readiness probe —
pointed at a path that returns a non-200 status. The pods start and *appear* to
run (the container process is alive), but because the readiness probe never
succeeds, Kubernetes never adds them to the Service endpoints, so no traffic is
routed to them. This simulates a subtle but common real-world failure: a healthy
process that is invisible to the load balancer.

## How the failure was injected

The readiness probe was changed to hit a non-existent path:

```yaml
readinessProbe:
  httpGet:
    path: /this-path-does-not-exist   # returns 404
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 10
```

Applied and the deployment rolled out.

## Detection

1. **Requests to payments-worker failed** even though pods showed `Running`:
```bash
   kubectl get pods -l app=payments-worker
   # STATUS: Running   READY: 0/1   ← running but NOT ready
```
   The `READY 0/1` column is the key signal — the container is running but
   failing readiness.

2. **The Service had zero endpoints:**
```bash
   kubectl get endpoints payments-worker
   # ENDPOINTS: <none>     ← no ready pods, so no endpoints
```

3. **Prometheus `up` metric** for payments-worker also reflected scrape
   failures, since the scrape target was not ready.

📸 Screenshot: `docs/screenshots/incident-05-not-ready.png`

## Investigation

This incident is a great illustration of the Kubernetes Service → endpoint →
pod routing chain:

1. **Pods were Running but not Ready.** A Running pod isn't necessarily serving
   traffic — readiness gates that.

2. **Checked why readiness was failing:**
```bash
   kubectl describe pod <payments-worker-pod>
   # Warning  Unhealthy  Readiness probe failed: HTTP probe failed
   #          with statuscode: 404
```
   The probe was hitting a 404 path.

3. **Traced the routing logic:** Because readiness failed, the EndpointSlice
   controller never added these pods to the Service's endpoints. With no
   endpoints, kube-proxy had no backends to route ClusterIP traffic to — so
   callers got connection failures despite "running" pods.

## Root Cause

The readiness probe was configured to check a path (`/this-path-does-not-exist`)
that returned 404. Kubernetes correctly interpreted the pod as not ready and
excluded it from Service endpoints, removing it from the traffic path. The
process was healthy; the *probe configuration* was wrong.

## Resolution

The readiness probe was corrected to point at the real health endpoint
(`/healthz`) and the deployment was re-applied. Pods transitioned to `READY 1/1`,
the EndpointSlice controller added them to the Service endpoints, kube-proxy
programmed the routing rules, and traffic flowed normally.

## Prevention

- **Endpoint-count alerting:** alert when a Service has zero ready endpoints —
  catches this class of failure regardless of cause.
```promql
  kube_endpoint_address_available{endpoint="payments-worker"} == 0
```
- **Probe configuration in deployment review:** readiness/liveness paths and
  timings should be reviewed as part of any deployment change, especially when
  startup logic or routes change.
- **Distinguish liveness vs readiness:** a misconfigured *liveness* probe causes
  restart loops (CrashLoopBackOff); a misconfigured *readiness* probe causes
  silent traffic loss. Knowing the difference speeds diagnosis.

## Reflection

The most valuable lesson: **"Running" is not "Ready," and "Ready" is what
determines traffic.** This incident reinforced the full Service-to-pod routing
chain — readiness gates endpoint membership, endpoints drive kube-proxy rules,
and kube-proxy rules determine where ClusterIP traffic goes. A pod can be
perfectly healthy and still receive zero traffic if readiness is misconfigured.
Alerting on ready-endpoint count catches this whole class of problem cheaply.
