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

## API Table

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check endpoint |
| POST | `/api/complaints` | Submit a new complaint |
| GET | `/api/complaints` | List complaints with optional filtering |
| GET | `/api/complaints/{id}` | Get details of a specific complaint |
| GET | `/api/stats` | Get application statistics |

## Demo Video
[Link to Demo Video (Placeholder)](https://youtube.com/placeholder)
