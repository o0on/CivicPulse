# ADR 0002: Frontend Runtime Configuration via Nginx Proxy

**Date:** 2026-09-26
**Status:** Accepted

## Context
The React frontend needs to know the URL of the FastAPI backend to make API calls. Traditionally, this is injected at build time using environment variables (e.g., `VITE_API_URL`). However, this violates the "build once, deploy anywhere" principle, requiring different Docker images for staging and production.

## Decision
We decided to configure the React app to make API calls to relative paths (e.g., `/api/complaints`). We then use Nginx as a reverse proxy in the frontend container to route all `/api/*` traffic to the backend service.

## Rationale
1. **Environment Agnostic Images:** The compiled static files contain no hardcoded URLs. The same Docker image can be deployed to local, staging, and production environments.
2. **CORS Mitigation:** Because the browser communicates solely with the Nginx server on the same domain/port, we eliminate Cross-Origin Resource Sharing (CORS) issues entirely.
3. **Simplicity:** It pushes the routing complexity to Nginx, which is highly optimized for this task, keeping the frontend code simpler.

## Consequences
- **Positive:** Simplified CI/CD pipeline and local development (via Docker Compose).
- **Negative:** The frontend container now runs a web server (Nginx) instead of just serving static files from a CDN or S3 bucket, slightly increasing the operational footprint.
