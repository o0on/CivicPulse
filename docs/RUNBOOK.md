# CivicPulse Runbook

## Deployment

### Local Deployment
1. Ensure Docker and Docker Compose are installed.
2. Run `docker compose up --build -d`.
3. The app will be available at `http://localhost:8080`.

### Production Deployment (Kubernetes)
Deployment is handled automatically by GitHub Actions on push to the `main` branch.
To manually deploy a specific configuration:
1. Ensure your `kubectl` context is set correctly.
2. Run `kubectl apply -k k8s/overlays/prod/`.

## Rollback Procedures

If a bad deployment goes out, you can roll back the deployment in Kubernetes.

1. Find the previous revision:
   ```bash
   kubectl rollout history deployment/backend -n civicpulse
   ```
2. Undo the rollout:
   ```bash
   kubectl rollout undo deployment/backend -n civicpulse
   ```
3. Verify the pods are running the previous stable image:
   ```bash
   kubectl get pods -n civicpulse
   ```

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

### Database Vacuum and Index Maintenance
Periodic ANALYZE and REINDEX operations maintain query performance across composite status/priority indexes.

### Redis AOF Persistence Recovery
Redis AOF rewrite occurs automatically to compact append-only logs while preserving cache state.
