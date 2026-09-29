# CivicPulse Runbook

## Deployment

### Local Deployment
1. Ensure Docker and Docker Compose are installed.
2. Run `docker compose up --build -d`.
3. The frontend is accessible at `http://localhost:3000` (or `http://127.0.0.1:3000`).

### Production Deployment (Kubernetes)
Deployment is handled automatically by GitHub Actions on push to the `main` branch.
To manually deploy a specific configuration:
1. Ensure your `kubectl` context is set correctly.
2. Run `kubectl apply -k k8s/overlays/prod/`.

## Rollback Procedures

CivicPulse supports two distinct rollback mechanisms depending on the operational context:

### Mechanism 1: Fast Imperative Rollback (`kubectl rollout undo`)
* **When to use**: The **3:00 AM emergency answer**. When production is actively degraded or throwing errors, you need immediate recovery in seconds without waiting for a CI/CD build cycle.
* **Procedure**:
  1. Inspect deployment revision history:
     ```bash
     kubectl rollout history deployment/backend -n civicpulse
     ```
  2. Roll back immediately to the previous deployment revision:
     ```bash
     kubectl rollout undo deployment/backend -n civicpulse
     kubectl rollout undo deployment/frontend -n civicpulse
     ```
  3. Verify status:
     ```bash
     kubectl rollout status deployment/backend -n civicpulse
     kubectl get pods -n civicpulse
     ```

### Mechanism 2: Declarative Git-Audited Rollback (Previous Commit SHA)
* **When to use**: The **correct, auditable answer once the fire is out**. Restores synchronization between Git repository state and cluster state so that future CI/CD runs don't overwrite the rollback.
* **Procedure**:
  1. Identify the last known good commit SHA from git history (`git log --oneline -n 5`).
  2. Re-apply the manifest using the known-good image SHA:
     ```bash
     cd k8s/overlays/prod
     kustomize edit set image \
       ghcr.io/YOUR_ORG/civicpulse-backend=ghcr.io/o0on/civicpulse-backend:<PREVIOUS_STABLE_SHA> \
       ghcr.io/YOUR_ORG/civicpulse-frontend=ghcr.io/o0on/civicpulse-frontend:<PREVIOUS_STABLE_SHA>
     kubectl apply -k .
     ```
  3. Alternatively, revert the commit in Git (`git revert <BAD_COMMIT_SHA>`) and push to `main` so the automated CD pipeline redeploys the stable SHA declaratively.


## Checking Logs

### Kubernetes
To view backend logs:
```bash
kubectl logs -l app=backend -n civicpulse -f
```

To view frontend (Nginx) logs:
```bash
kubectl logs -l app=frontend -n civicpulse -f
```

### Docker Compose
```bash
docker compose logs -f backend
```

## Triage Engine Troubleshooting

If the triage engine starts failing (e.g., external LLM API is down or rate limits are exhausted):

1. **Switch Providers manually:** 
   Update the `TRIAGE_PROVIDER` environment variable in the Kubernetes ConfigMap (`k8s/base/configmap.yaml`) or `.env` file to another provider:
   ```yaml
   TRIAGE_PROVIDER: "gemini" # Options: groq, gemini, dummy
   ```
   Apply the change: `kubectl apply -f k8s/base/configmap.yaml` and restart the backend deployment: `kubectl rollout restart deployment backend -n civicpulse`.

2. **Enable Dummy Fallback:**
   If all external APIs are unreachable, switch `TRIAGE_PROVIDER` to `dummy`. This uses a deterministic Python fallback that assigns priority based on keyword matching (e.g., "pothole" -> High) without making external network calls.

### Emergency Triage Provider Failover
When external LLM APIs fail, the triage service automatically falls back to deterministic rule matching without downtime.

### Database Migrations
Database schema updates are managed using Alembic. To manually run or inspect migrations inside Kubernetes:
```bash
# Apply pending migrations
kubectl exec -n civicpulse deployment/backend -- /bin/sh -c "cd /app && alembic upgrade head"

# Verify current revision
kubectl exec -n civicpulse deployment/backend -- /bin/sh -c "cd /app && alembic current"
```

### Database Vacuum and Index Maintenance
Periodic ANALYZE and REINDEX operations maintain query performance across composite status/priority indexes.

### Redis AOF Persistence Recovery
Redis AOF rewrite occurs automatically to compact append-only logs while preserving cache state.
