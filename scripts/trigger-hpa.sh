#!/bin/bash
set -euo pipefail

# CivicPulse — Automated HPA Scale-Up Trigger Script
# Runs high-concurrency traffic through backend service to cross the 60% CPU threshold.

NAMESPACE="civicpulse"
DEPLOYMENT="backend"
PORT=8000

echo "=== CivicPulse HPA Scale-Up Trigger ==="

# 1. Start port-forwarding in background if not already active
if ! curl -sf "http://localhost:${PORT}/health" >/dev/null 2>&1; then
    echo "Starting port-forward for backend service on port ${PORT}..."
    kubectl port-forward -n "${NAMESPACE}" "svc/${DEPLOYMENT}" "${PORT}:${PORT}" &
    PF_PID=$!
    trap 'kill ${PF_PID} 2>/dev/null || true' EXIT
    sleep 3
fi

echo "Verifying backend health on port ${PORT}..."
curl -sf "http://localhost:${PORT}/health" || (echo "Backend unreachable!" && exit 1)

echo "Starting high-concurrency k6 traffic against CivicPulse..."
echo "Watch your HPA in another terminal via: kubectl get hpa -n civicpulse -w"

k6 run --env "BASE_URL=http://localhost:${PORT}" load/k6-script.js

echo "=== Load generation complete ==="
