#!/usr/bin/env bash
# ==============================================================================
# CivicPulse Local Kubernetes Manager (Kind)
# ==============================================================================
set -euo pipefail

CLUSTER_NAME="civicpulse"
NAMESPACE="civicpulse"

action="${1:-status}"

case "$action" in
  start)
    echo "=== Starting CivicPulse in Local Kubernetes ==="
    # Check if cluster exists
    if ! kind get clusters 2>/dev/null | grep -q "^${CLUSTER_NAME}$"; then
      echo "Creating Kind cluster '${CLUSTER_NAME}'..."
      kind create cluster --name "${CLUSTER_NAME}"
    fi

    # Ensure metrics-server is installed for HPA
    if ! kubectl get deployment metrics-server -n kube-system >/dev/null 2>&1; then
      echo "Installing metrics-server for HPA..."
      kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
      kubectl patch deployment metrics-server -n kube-system --type 'json' -p '[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]'
    fi

    # Ensure VPA CRDs are installed
    if ! kubectl get crd verticalpodautoscalers.autoscaling.k8s.io >/dev/null 2>&1; then
      echo "Installing VPA CRDs..."
      kubectl apply -f https://raw.githubusercontent.com/kubernetes/autoscaler/master/vertical-pod-autoscaler/deploy/vpa-v1-crd-gen.yaml
    fi

    echo "Building local images..."
    docker build -t "ghcr.io/o0on/civicpulse-backend:local" ./backend
    docker build -t "ghcr.io/o0on/civicpulse-frontend:local" ./frontend

    echo "Loading images into Kind..."
    kind load docker-image "ghcr.io/o0on/civicpulse-backend:local" --name "${CLUSTER_NAME}"
    kind load docker-image "ghcr.io/o0on/civicpulse-frontend:local" --name "${CLUSTER_NAME}"

    echo "Applying secrets and manifests..."
    kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -
    GEMINI_KEY="${GEMINI_API_KEY:-$(grep '^GEMINI_API_KEY=' .env 2>/dev/null | cut -d= -f2- || true)}"
    kubectl create secret generic civicpulse-secrets \
      --namespace "${NAMESPACE}" \
      --from-literal=DATABASE_URL=postgresql+asyncpg://civicpulse:civicpulse_dev@postgres.civicpulse.svc.cluster.local:5432/civicpulse \
      --from-literal=REDIS_URL=redis://redis.civicpulse.svc.cluster.local:6379/0 \
      --from-literal=SECRET_KEY=dev-secret-key-civicpulse \
      --from-literal=GROQ_API_KEY="" \
      --from-literal=GEMINI_API_KEY="${GEMINI_KEY}" \
      --from-literal=POSTGRES_USER=civicpulse \
      --from-literal=POSTGRES_PASSWORD=civicpulse_dev \
      --dry-run=client -o yaml | kubectl apply -f -

    kubectl apply -k k8s/overlays/dev
    echo "Waiting for rollout..."
    kubectl rollout status statefulset/postgres -n "${NAMESPACE}" --timeout=120s
    kubectl rollout status deployment/redis -n "${NAMESPACE}" --timeout=120s
    kubectl rollout status deployment/backend -n "${NAMESPACE}" --timeout=120s
    kubectl rollout status deployment/frontend -n "${NAMESPACE}" --timeout=120s

    echo "Running database migrations..."
    kubectl exec -n "${NAMESPACE}" deployment/backend -- /bin/sh -c "cd /app && alembic upgrade head"
    echo "Kubernetes deployment ready!"
    ;;

  status)
    echo "=== CivicPulse Kubernetes Status ==="
    kubectl get pods,svc,hpa,pdb -n "${NAMESPACE}"
    ;;

  stop)
    echo "=== Stopping CivicPulse Local Kubernetes ==="
    kind delete cluster --name "${CLUSTER_NAME}"
    echo "Cluster deleted."
    ;;

  *)
    echo "Usage: $0 {start|status|stop}"
    exit 1
    ;;
esac
