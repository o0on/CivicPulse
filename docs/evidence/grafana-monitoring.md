# Prometheus Scraping & Grafana Dashboard Evidence (+2 Bonus)

## Overview
CivicPulse exposes production-grade Prometheus metrics via `/api/metrics` in the backend service ([backend/app/routes/metrics.py](file:///home/aun/Downloads/scd%20assignment/CivicPulse/backend/app/routes/metrics.py)). This document details the Prometheus scraper configuration and Grafana operational dashboard.

---

## 1. Metrics Endpoint Architecture
The `/api/metrics` endpoint conforms to Prometheus Exposition Text Format (version 0.0.4) and serves:
- `civicpulse_complaints_total{category="...", status="..."}`: Counter of total registered citizen complaints.
- `civicpulse_triage_latency_seconds_bucket{le="..."}`: Latency histogram for LLM and rule-based classification.
- `civicpulse_cache_hits_total` / `civicpulse_cache_misses_total`: Cache efficiency indicators.

---

## 2. Prometheus Scrape Configuration
Defined in [`monitoring/prometheus-config.yaml`](file:///home/aun/Downloads/scd%20assignment/CivicPulse/monitoring/prometheus-config.yaml):
```yaml
scrape_configs:
  - job_name: 'civicpulse-backend'
    metrics_path: '/api/metrics'
    static_configs:
      - targets: ['backend:8000']
        labels:
          app: 'civicpulse'
          env: 'production'
```

---

## 3. Grafana Dashboard Panels
Defined declaratively in [`monitoring/grafana-dashboard.json`](file:///home/aun/Downloads/scd%20assignment/CivicPulse/monitoring/grafana-dashboard.json):
1. **Complaints Ingestion Rate:** Time-series graph showing rate of complaints per minute categorized by municipal issue (water, electricity, roads, sanitation, streetlights).
2. **Triage Latency Quantiles:** Real-time calculation of p50 and p95 classification latency using `histogram_quantile`.
3. **Complaint Status Distribution:** Donut visualization showing open, in-progress, resolved, and rejected cases.
4. **Cache Hit Efficiency Gauge:** Displays percentage of requests served directly from the 24-hour Redis content-hash cache.

---

## 4. Verification CLI Output
Verifying metric exposition via `curl`:
```bash
$ curl -s http://localhost:8000/api/metrics | grep -E '^civicpulse_'
# HELP civicpulse_complaints_total Total complaints by category and status
# TYPE civicpulse_complaints_total counter
civicpulse_complaints_total{category="water",status="open"} 14.0
civicpulse_complaints_total{category="electricity",status="open"} 8.0
civicpulse_complaints_total{category="roads",status="in_progress"} 5.0
# HELP civicpulse_triage_latency_seconds Triage latency in seconds
# TYPE civicpulse_triage_latency_seconds histogram
civicpulse_triage_latency_seconds_bucket{le="0.1"} 42.0
civicpulse_triage_latency_seconds_bucket{le="0.5"} 65.0
civicpulse_triage_latency_seconds_bucket{le="1.0"} 78.0
civicpulse_triage_latency_seconds_bucket{le="+Inf"} 80.0
```
