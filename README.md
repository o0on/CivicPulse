# CivicPulse

## Problem Statement
CivicPulse is a modern 3-tier web application built to collect, triage, and visualize municipal complaints (e.g., potholes, broken streetlights). Given the overwhelming number of unstructured complaints submitted to city councils, CivicPulse uses an intelligent triage engine (leveraging LLMs) to automatically categorize complaints, assign priority, and extract location entities. This allows city officials to efficiently allocate resources and address the most critical issues first.

## Badges
![CI Status](https://img.shields.io/github/actions/workflow/status/username/CivicPulse/ci.yml?branch=main&label=CI)
![CD Status](https://img.shields.io/github/actions/workflow/status/username/CivicPulse/cd.yml?branch=main&label=CD)
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

## Quickstart

To build and run the entire application locally using Docker Compose:

```bash
docker compose up --build -d
```

This will spin up:
- Frontend at `http://localhost:8080`
- Backend API at `http://localhost:8000` (Docs at `http://localhost:8000/docs`)
- Redis at `localhost:6379`
- PostgreSQL at `localhost:5432`

To shut down:
```bash
docker compose down -v
```

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
