# CivicPulse

## Problem Statement
CivicPulse is a modern 3-tier web application built to collect, triage, and visualize municipal complaints (e.g., potholes, broken streetlights). Given the overwhelming number of unstructured complaints submitted to city councils, CivicPulse uses an intelligent triage engine (leveraging LLMs) to automatically categorize complaints, assign priority, and extract location entities. This allows city officials to efficiently allocate resources and address the most critical issues first.

## Badges
![CI Status](https://img.shields.io/github/actions/workflow/status/o0on/CivicPulse/ci.yml?branch=main&label=CI)
![CD Status](https://img.shields.io/github/actions/workflow/status/o0on/CivicPulse/cd.yml?branch=main&label=CD)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

## Architecture

```mermaid
flowchart TD
    User([User])
    subgraph K8s Cluster
        Ingress([Ingress Controller])
        Nginx[Frontend (React + Nginx)]
        FastAPI[Backend (FastAPI)]
        Redis[(Redis - Rate Limiting & Cache)]
        Postgres[(PostgreSQL - Primary DB)]
        TriageEngine{Triage Engine}
        
        User -->|HTTP/HTTPS| Ingress
        Ingress -->|/api/*| FastAPI
        Ingress -->|/*| Nginx
        FastAPI <--> Redis
        FastAPI <--> Postgres
        FastAPI <--> TriageEngine
    end
    
    TriageEngine -.-> |API Call| Groq/Gemini/OpenAI([External LLM Providers])
```

## Quickstart & Deployment

CivicPulse supports two execution methods: **Docker Compose** (for standard local development) and **Local Kubernetes** (for simulating production orchestration).

### Method 1: Docker Compose (Local Development)

The fastest way to run the entire application stack (Frontend, Backend, PostgreSQL, Redis) locally:

```bash
# 1. Copy environment variables
cp .env.example .env

# 2. Build and start services in the background
docker compose up --build -d
```

- **Frontend UI**: [http://localhost:3000](http://localhost:3000)
- **API Health Check**: [http://localhost:3000/api/health](http://localhost:3000/api/health)
- **Readiness Probe**: [http://localhost:3000/api/ready](http://localhost:3000/api/ready)

To shut down and clean up containers:
```bash
docker compose down -v
```

---

### Method 2: Local Kubernetes via Kind (Production-grade Simulation)

To test the complete Kubernetes architecture locally (Deployments, StatefulSets, persistent volumes, health probes, and automated database migrations):

```bash
# 1. Start the cluster, build & load images, apply manifests, and run migrations
./scripts/k8s-local.sh start

# 2. Forward the frontend service port to localhost
kubectl port-forward -n civicpulse svc/frontend 3000:80
```

- **Frontend UI**: [http://localhost:3000](http://localhost:3000)
- **Check Cluster Status**:
  ```bash
  ./scripts/k8s-local.sh status
  ```

To stop and delete the local Kubernetes cluster:
```bash
./scripts/k8s-local.sh stop
```

> **Note**: Both methods expose the frontend on port `3000`. Stop one before starting the other to avoid port collision.

### Backend Framework
CivicPulse backend is implemented using **FastAPI** (Python 3.12) rather than Flask to leverage native asynchronous I/O (`async`/`await` with `asyncpg` and Redis), automatic Pydantic request/response schema validation, and high-performance non-blocking query pipelines.

## API Table

| Method | Endpoint | Description | Cache / Behavior |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` / `/api/health` | Liveness health check | Returns `200 OK` (Zero DB dependency) |
| `GET` | `/ready` / `/api/ready` | Readiness health check | Validates live PostgreSQL & Redis connections |
| `GET` | `/api/meta/providers` | Active triage provider & history | Surfaces active LLM, fallback status, and last 20 triage latencies |
| `POST` | `/api/complaints` | Submit new municipal complaint | Rate-limited (15 req/min), automated AI triage + fallback |
| `GET` | `/api/complaints` | List paginated complaints | Filterable by `status`, `category`, and `priority` |
| `GET` | `/api/complaints/{id}` | Get specific complaint by UUID | Full complaint model with triage metadata |
| `PATCH` | `/api/complaints/{id}/status` | Transition complaint status | Enforces valid state machine transitions (returns `409` on invalid) |
| `GET` | `/api/stats` | Aggregated complaint statistics | Cached in Redis (TTL 30s) with `X-Cache: HIT/MISS` headers |
| `GET` | `/api/metrics` | Prometheus metrics endpoint | Scrapes real-time complaint volumes and triage latencies |

---

## Submission & Verification Artifacts

* **Repository URL:** [https://github.com/o0on/CivicPulse](https://github.com/o0on/CivicPulse)
* **Latest Passing CI Pipeline:** [CI Run #36601422477](https://github.com/o0on/CivicPulse/actions/runs/36601422477)
* **Latest Passing CD Pipeline:** [CD Run #36601422656](https://github.com/o0on/CivicPulse/actions/runs/36601422656)
* **GHCR Container Images:**
  - `ghcr.io/o0on/civicpulse-backend:6d9c4b0`
  - `ghcr.io/o0on/civicpulse-frontend:6d9c4b0`
* **Contribution Balance (`git shortlog -sn --all`):**
  - `51  o0on`
  - `42  mazhar3077`
  *(Both contributors exceed the required 35-commit minimum with balanced distribution).*

---

## Evidence & Verification Documents

Detailed documentation and test evidence are located in [`docs/`](docs/) and [`docs/evidence/`](docs/evidence/):
- **Branch Protection Rules:** [`docs/evidence/branch-protection.md`](docs/evidence/branch-protection.md)
- **Merge Conflict Resolution:** [`docs/evidence/merge-conflict-resolution.md`](docs/evidence/merge-conflict-resolution.md)
- **Blocked Merge (Red $\rightarrow$ Green):** [`docs/evidence/blocked-merge.md`](docs/evidence/blocked-merge.md)
- **HPA Autoscaling & Load Verification:** [`docs/evidence/hpa-scaling.md`](docs/evidence/hpa-scaling.md)
- **Zero-Downtime Rolling Update Demonstration:** [`docs/evidence/zero-downtime.md`](docs/evidence/zero-downtime.md)
- **Architectural Decision Records (ADRs):** [`docs/adr/`](docs/adr/)
- **Engineering Notes & Design Questions:** [`docs/ENGINEERING-NOTES.md`](docs/ENGINEERING-NOTES.md)
- **Operational Runbook:** [`docs/RUNBOOK.md`](docs/RUNBOOK.md)

---

## Demo Video
[Link to Demo Walkthrough Video](https://youtube.com/placeholder)
*(Video duration: $\le 5$ minutes, covers clean clone, Docker Compose and K8s startup, AI triage with fallback, rate limiting, HPA autoscaling, and rollback).*

