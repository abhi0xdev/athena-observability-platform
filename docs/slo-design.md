# checkout-api SLO Design

## Service

checkout-api

## User Journey

Processes checkout requests for customer orders.

## Service Level Indicator (SLI)

Availability

success_requests / total_requests

PromQL:

sum(rate(http_requests_total{status!~"5.."}[5m]))
/
sum(rate(http_requests_total[5m]))

## Service Level Objective (SLO)

99.5% availability over a rolling 30-day window.

## Error Budget

100% - 99.5% = 0.5%

0.5% of 30 days = 216 minutes allowable downtime per month.

## Alerting Strategy

Fast Burn:

* 5m + 1h windows
* 14.4x burn rate
* Critical severity

Slow Burn:

* 30m + 6h windows
* 6x burn rate
* Warning severity

## Observability Stack

* Prometheus
* Grafana
* Loki
* Tempo
* OpenTelemetry Collector

## Outcome

The platform can detect rapid and gradual consumption of the error budget before the SLO is violated.
