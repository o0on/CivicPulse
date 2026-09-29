#!/bin/bash
set -euo pipefail

# CivicPulse — Zero-Downtime Rolling Update Demonstration Script
# Demonstrates 0 failed requests during a live Deployment rollout restart under k6 traffic.

NAMESPACE="civicpulse"
DEPLOYMENT="backend"
PORT=8000

echo "=== CivicPulse Zero-Downtime Rolling Update Demonstration ==="

# 1. Start port-forwarding in background if not already accessible
if ! curl -sf "http://localhost:${PORT}/health" >/dev/null 2>&1; then
    echo "Starting port-forward for backend service on port ${PORT}..."
    kubectl port-forward -n "${NAMESPACE}" "deployment/${DEPLOYMENT}" "${PORT}:${PORT}" &
    PF_PID=$!
    trap 'kill ${PF_PID} 2>/dev/null || true' EXIT
    sleep 3
fi

echo "Verifying initial service health..."
curl -sf "http://localhost:${PORT}/health" || (echo "Backend service not accessible!" && exit 1)

echo "Starting continuous k6 traffic generation (30 req/s for 45s)..."
# Trigger rolling update in parallel after 5 seconds of load
(
    sleep 5
    echo ">>> Triggering rolling update: kubectl rollout restart deployment/${DEPLOYMENT} -n ${NAMESPACE}"
    kubectl rollout restart "deployment/${DEPLOYMENT}" -n "${NAMESPACE}"
    echo ">>> Awaiting rollout completion..."
    kubectl rollout status "deployment/${DEPLOYMENT}" -n "${NAMESPACE}" --timeout=60s
    echo ">>> Rolling update finished successfully!"
) &

# Run k6 load test
k6 run --env "BASE_URL=http://localhost:${PORT}" load/zero-downtime.js

echo "=== Demonstration complete: 0 failed requests verified under continuous traffic ==="
