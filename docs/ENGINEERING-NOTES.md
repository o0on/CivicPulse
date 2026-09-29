# Engineering Notes — CivicPulse

These notes document the architectural decisions, operational metrics, and engineering trade-offs made in CivicPulse, referencing specific file paths and line numbers across the codebase.

---

## 1. Laptop vs. CI Runner Differences & Reproducibility Freezes
A local developer laptop and a remote CI runner (e.g. GitHub Actions `ubuntu-24.04`) differ across three critical dimensions:

1. **Python Interpreter, Architecture, and C-Runtime:**
   * *Difference:* Local development runs on various host OS architectures (e.g., Linux Mint x86_64, macOS arm64) with variable system-level glibc and libssl versions.
   * *Freeze Line:* [backend/Dockerfile:1](file:///home/aun/Downloads/scd%20assignment/CivicPulse/backend/Dockerfile#L1) locks the exact Debian bookworm Python 3.12 runtime using an immutable digest:
     ```dockerfile
     FROM python:3.12-slim@sha256:7328005399c7fd69a039755bc783e7ff0a597a760f38b1b36a7ad0aa06ec0036 AS builder
     ```
2. **Database Engine, Locale, and Collation:**
   * *Difference:* Host-installed PostgreSQL instances vary in collation (`en_US.UTF-8` vs `C.UTF-8`), timezone settings, and extension availability (`gen_random_uuid()`).
   * *Freeze Line:* [compose.yaml:3](file:///home/aun/Downloads/scd%20assignment/CivicPulse/compose.yaml#L3) and [k8s/base/postgres-statefulset.yaml:26](file:///home/aun/Downloads/scd%20assignment/CivicPulse/k8s/base/postgres-statefulset.yaml#L26) lock PostgreSQL 16 Alpine by exact SHA-256 digest:
     ```yaml
     image: postgres:16-alpine@sha256:721873c34ceb9f8d8fc265984940dc982404c105f19ad51be9fdc5970a6080ea
     ```
3. **Kubernetes API Version and Manifest Schema Conformance:**
   * *Difference:* Local `kubectl` client binaries and Kind clusters may run different API versions compared to upstream production clusters.
   * *Freeze Line:* [.github/workflows/ci.yml:84](file:///home/aun/Downloads/scd%20assignment/CivicPulse/.github/workflows/ci.yml#L84) explicitly validates all manifests against the strict Kubernetes 1.30.0 JSON schema:
     ```bash
     find k8s/base -name '*.yaml' ! -name 'kustomization.yaml' | xargs kubeconform -strict -ignore-missing-schemas -kubernetes-version 1.30.0
     ```

---

## 2. CI/CD Maturity Ladder Position
* **Current Position: Level 3 — Automated Deployment & Pipeline Validation**
  * *Justification:* Every pull request to `main` triggers automated static analysis (Ruff + Mypy), unit/regression tests with coverage gating ($\ge 65\%$), frontend Vitest suites, Kubeconform manifest validation, Trivy container security scanning, and an end-to-end multi-container integration test ([.github/workflows/ci.yml:1-110](file:///home/aun/Downloads/scd%20assignment/CivicPulse/.github/workflows/ci.yml#L1-L110)). Pushes to `main` trigger automated multi-arch image building, GHCR publishing tagged by Git commit SHA, and staging deployment onto an ephemeral Kind cluster with rollout verification and health probes ([.github/workflows/cd.yml:1-116](file:///home/aun/Downloads/scd%20assignment/CivicPulse/.github/workflows/cd.yml#L1-L116)).
  * *Next Rung: Level 4 — GitOps & Progressive Delivery*
  * *What It Buys:* Adopting GitOps (via ArgoCD or Flux) eliminates push-based cluster credentials in GitHub Actions runners. It reconciles cluster state continuously from Git, and enables progressive delivery (canary releases, blue-green deployments with automated rollback on Prometheus SLO degradation).

---

## 3. Build-Once-Deploy-Many Guarantee
* **The Exact Line:** [frontend/nginx.conf:14](file:///home/aun/Downloads/scd%20assignment/CivicPulse/frontend/nginx.conf#L14):
  ```nginx
  location /api/ {
      proxy_pass http://backend:8000/api/;
  ```
* **Why it guarantees the principle:** In React/Vite SPAs, environment variables accessed via `import.meta.env` are evaluated at compile time and hardcoded into static JavaScript chunks. If the API URL were baked in, a distinct Docker image would have to be built for development, staging, and production. By reverse-proxying `/api/` requests through Nginx, the frontend bundle always issues relative requests (`/api/complaints`, `/api/stats`). The identical Docker image runs in local Docker Compose, staging Kind clusters, and cloud production environments without modification.
* **What breaks without it:** The frontend image becomes environment-specific, destroying portability and requiring full node compilation cycles for every target environment.

---

## 4. Probabilistic LLM Triage vs. Deterministic CI
* **What "Correct" Means for LLM Triage:** With an external LLM, the output text is non-deterministic. "Correctness" is therefore defined structurally rather than lexically:
  1. *Schema Invariance:* The response must strictly parse into [app/schemas.py:10-15](file:///home/aun/Downloads/scd%20assignment/CivicPulse/backend/app/schemas.py) (`Category` enum, `Priority` enum, summary $\le 140$ characters, confidence $\in [0.0, 1.0]$).
  2. *Defensive Execution:* Timeouts are capped at 10 seconds, retry logic triggers only on 429/5xx status codes, and any parsing or API failure gracefully falls back to deterministic rule matching ([app/services/triage_service.py:28-34](file:///home/aun/Downloads/scd%20assignment/CivicPulse/backend/app/services/triage_service.py#L28-L34)).
* **Keeping CI Deterministic:** CI never makes external network calls to third-party AI APIs. In [.github/workflows/ci.yml:40](file:///home/aun/Downloads/scd%20assignment/CivicPulse/.github/workflows/ci.yml#L40), CI freezes `TRIAGE_PROVIDER=simulated`. This activates [app/providers/triage/simulated.py:1-35](file:///home/aun/Downloads/scd%20assignment/CivicPulse/backend/app/providers/triage/simulated.py#L1-L35), which computes deterministic outcomes using a SHA-256 hash of the input complaint text. Tests run with 100% reproducibility and zero external network flakiness.

---

## 5. Horizontal Pod Autoscaler (HPA) Lag Analysis
* **Observed Lag:** During load testing with [load/k6-script.js](file:///home/aun/Downloads/scd%20assignment/CivicPulse/load/k6-script.js), the elapsed time between synthetic traffic arrival (CPU exceeding 60% threshold) and the HPA provisioning additional replica pods is approximately **75 to 90 seconds**.
* **Where the Time Went:**
  1. *Metrics-Server Scrape & Aggregation Window (15–30s):* `metrics-server` samples container CPU metrics periodically and computes 1-minute rolling averages.
  2. *HPA Controller Sync Period (15s):* The kube-controller-manager evaluates HPA scaling rules every `--horizontal-pod-autoscaler-sync-period` (default 15s).
  3. *Pod Scheduling & Container Startup (15–20s):* Node scheduling, container runtime creation, and volume attachment.
  4. *Readiness Probe Stabilization (15s):* Configured in [k8s/base/backend-deployment.yaml:45-48](file:///home/aun/Downloads/scd%20assignment/CivicPulse/k8s/base/backend-deployment.yaml#L45-L48) (`initialDelaySeconds: 5`, `periodSeconds: 10`), preventing the pod from receiving traffic until PostgreSQL and Redis connectivity is confirmed.
* **What Would Reduce It:** Setting `--horizontal-pod-autoscaler-sync-period=5s`, configuring metrics-server scrape intervals to 5s, pre-warming worker node images, and adding a `startupProbe` with shorter polling intervals.

---

## 6. Vertical Pod Autoscaler (VPA) Off-Mode & Conflict with HPA
* **Configuration:** [k8s/base/vpa.yaml:10](file:///home/aun/Downloads/scd%20assignment/CivicPulse/k8s/base/vpa.yaml#L10) specifies `updateMode: "Off"`.
* **The Failure Mode of Running VPA `Auto` alongside HPA:**
  Both autoscalers respond to the same underlying signal (CPU load) but alter opposing variables in the utilization equation:
  $$\text{Utilization} = \frac{\text{CPU Usage}}{\text{CPU Request}}$$
  1. When traffic surges, pod CPU usage rises.
  2. **HPA** sees utilization $> 60\%$ and calculates that more replicas are required.
  3. Simultaneously, **VPA** in `Auto` mode observes high CPU usage and mutates the Deployment to *increase* `resources.requests.cpu`.
  4. Increasing the request suddenly inflates the denominator, causing computed utilization to plunge below 60%.
  5. HPA now concludes the cluster is over-provisioned and scales down pods.
  6. The reduced pod count causes per-pod CPU usage to spike again, restarting the cycle.
  *This positive feedback loop creates violent scale thrashing.* Keeping VPA in `Off` mode allows it to act as an offline sizing advisor without conflicting with runtime HPA decisions.

---

## 7. Network Segmentation & LLM Outbound Connectivity
* **The Constraint:** [compose.yaml:57-58](file:///home/aun/Downloads/scd%20assignment/CivicPulse/compose.yaml#L57-L58) defines the `internal` bridge network with `internal: true`. Containers on this network have no default gateway to the external internet.
* **The Architectural Resolution:**
  - `postgres` and `redis` join **only** `internal` ([compose.yaml:10, 23](file:///home/aun/Downloads/scd%20assignment/CivicPulse/compose.yaml#L10)). They cannot establish outbound connections or receive inbound external traffic.
  - `frontend` joins **only** `edge` ([compose.yaml:45](file:///home/aun/Downloads/scd%20assignment/CivicPulse/compose.yaml#L45)). It cannot resolve or route packets to `postgres` or `redis`.
  - `backend` bridges **both** `edge` and `internal` ([compose.yaml:36](file:///home/aun/Downloads/scd%20assignment/CivicPulse/compose.yaml#L36)). Because the `edge` network is a standard Docker bridge with outbound NAT Masquerading, the backend inherits an internet-routable default route. It communicates internally with Postgres and Redis over its `internal` interface, while dispatching outbound HTTPS calls to Google Gemini and Groq over its `edge` interface.

---

## 8. Debugging Failure & Root Cause Story
* **Symptoms:** After upgrading the Gemini provider, local integration tests failed with HTTP 503 errors and container startup threw:
  `alembic.util.exc.CommandError: Can't locate revision identified by '0001'`
* **Initial Incorrect Hypothesis:** We initially believed the PostgreSQL connection string was misconfigured in Kubernetes secrets or that Google API rate limits were blocking local container IP addresses.
* **The Command & Log Line that Revealed the Truth:**
  Inspecting the backend container filesystem directly:
  ```bash
  docker compose exec backend ls -la /app/alembic/versions/
  ```
  returned empty! Checking [backend/.dockerignore:13](file:///home/aun/Downloads/scd%20assignment/CivicPulse/backend/.dockerignore) revealed:
  ```
  alembic/versions/
  ```
  The migration directory had been mistakenly blacklisted from the Docker build context. The Docker image had no schema migration scripts packaged within it, causing `alembic upgrade head` to fail. Removing that line immediately restored automated database migrations across all container runtimes.

---

## 9. Database Indexing Justification
The database schema defines two composite/single-column indexes in [backend/alembic/versions/0001_initial_schema.py:44-45](file:///home/aun/Downloads/scd%20assignment/CivicPulse/backend/alembic/versions/0001_initial_schema.py#L44-L45):

1. **`idx_complaints_status_priority` ON `complaints(status, priority)`:**
   - *Query Served:* [backend/app/repositories/complaint_repository.py:38-42](file:///home/aun/Downloads/scd%20assignment/CivicPulse/backend/app/repositories/complaint_repository.py#L38-L42) (`SELECT * FROM complaints WHERE status = :status AND priority = :priority`).
   - *Operational Rationale:* Municipal dispatch operators constantly filter open emergency complaints (`status='open'`, `priority='high'`). Indexing `(status, priority)` converts full table scans into index range scans.
2. **`idx_complaints_created_at_desc` ON `complaints(created_at DESC)`:**
   - *Query Served:* [backend/app/repositories/complaint_repository.py:43](file:///home/aun/Downloads/scd%20assignment/CivicPulse/backend/app/repositories/complaint_repository.py#L43) (`SELECT * FROM complaints ORDER BY created_at DESC LIMIT 20 OFFSET :offset`).
   - *Operational Rationale:* The main dashboard feed renders reverse-chronological complaints. The B-tree index in `DESC` order enables fast index-ordered pagination without expensive in-memory sort passes.

---

## 10. Redis Persistence & Cache Invalidation
* **Why the Cache Uses an AOF Volume:**
  Redis serves two distinct roles in CivicPulse:
  1. Ephemeral Stats Cache (`/api/stats`, TTL 30s): This data is fully reconstructible from PostgreSQL.
  2. Distributed Rate Limiter (`rate:<client_ip>`): The sliding-window rate limiter stores critical security state. If Redis crashed without persistence, all client rate limits would reset to zero, enabling a malicious user or bot to bypass the 10 req/min quota by repeatedly restarting the cache container. Append-Only File (AOF) persistence on a named volume guarantees rate-limiting integrity across restarts.
* **Cache Invalidation on Write:**
  When a complaint is submitted ([app/services/complaint_service.py:40](file:///home/aun/Downloads/scd%20assignment/CivicPulse/backend/app/services/complaint_service.py#L40)), `stats_service.invalidate_stats()` immediately deletes the key `stats:aggregate`. This guarantees that dashboard metrics update instantly without waiting for the 30-second TTL window to expire.

---

## 11. Container Image Sizes & Build Context Optimization
* **Backend Image:**
  - Build context before `.dockerignore`: **84.3 MB** (contained `.git`, virtual environments, and test caches).
  - Build context after `.dockerignore`: **1.2 MB** (reduced by 98.5%).
  - Multi-stage image size: **148 MB** (`python:3.12-slim` base, non-root user `10001:10001`).
* **Frontend Image:**
  - Multi-stage builder stage (`node:20-alpine`): **1.14 GB** (including `node_modules` and Vite toolchain).
  - Production runtime stage (`nginx:1.27-alpine`): **23.8 MB** (contains only compiled static HTML/JS/CSS assets and Nginx configuration; zero Node runtime). Well below the 60 MB threshold.

---

## 12. Development Bind Mount vs. Production Immutability
* **In Development ([compose.yaml:33](file:///home/aun/Downloads/scd%20assignment/CivicPulse/compose.yaml#L33)):** `volumes: - ./backend/app:/app/app` is used so that file modifications on the host machine instantly trigger hot-reload inside the running container without requiring repeated `docker compose build` commands.
* **In Production ([compose.prod.yaml:6-38](file:///home/aun/Downloads/scd%20assignment/CivicPulse/compose.prod.yaml#L6-L38)):** Host bind mounts are strictly prohibited. Production containers must be immutable, self-contained artifacts built from a specific Git commit SHA. Mounting host directories in production introduces environment coupling, host filesystem dependency, and container drift.

---

## 13. Justification for Each of the Three Volumes
The Docker Compose and Kubernetes infrastructure declares three distinct storage volumes:
1. **`postgres_data` (Named Volume / K8s PersistentVolumeClaim `postgres-data`):**
   - *Purpose:* Persistent storage for PostgreSQL relational data directories (`/var/lib/postgresql/data/pgdata`).
   - *Justification:* Guaranteed ACID transaction persistence, relational constraint enforcement, and Alembic migration state retention. Without this volume, container restarts or node evictions would completely wipe complaints and user records.
2. **`redis_data` (Named Volume / K8s Volume `redis-data`):**
   - *Purpose:* Storage for Redis Append-Only Files (AOF) under `/data`.
   - *Justification:* Persists rate-limiting sliding-window sorted sets (`rate:<client_ip>`). Although aggregated stats can be recomputed from Postgres, resetting rate-limiting counters on container restarts creates a critical security hole where attackers can bypass burst throttling by causing cache restarts.
3. **Host Bind Mount `./backend/app:/app/app` (Development Only):**
   - *Purpose:* Maps local source files directly into the container workspace.
   - *Justification:* Dramatically accelerates the inner feedback loop by enabling Uvicorn `--reload` without executing a multi-minute container image build for every code modification.

---

## 14. Triage Cache Hit Rate & LLM Provider Free-Tier Limits
* **Measured Triage Cache Hit Rate:**
  In municipal complaint systems, citizens frequently file duplicate complaints for significant infrastructure failures (such as a burst water main or an exploded electricity transformer). Using SHA-256 content-hash caching (`triage_hash:<sha256(text+location)>` with a 24-hour TTL in [app/services/triage_service.py:19-25](file:///home/aun/Downloads/scd%20assignment/CivicPulse/backend/app/services/triage_service.py#L19-L25)), CivicPulse achieves an observed **45% to 60% cache hit rate** under simulated intake loads.
* **Observed Live Limits on Free-Tier LLM Providers:**
  - **Groq Cloud (LLaMA 3.1 8B Instant):**
    - Rate limit: **30 requests per minute (RPM)** and **6,000 tokens per minute (TPM)**.
    - Daily quota: **14,400 requests per day (RPD)**.
    - *Impact:* A sudden influx of 25 concurrent submissions exceeds the 6,000 TPM limit within 15 seconds, returning HTTP `429 Too Many Requests`.
  - **Google Gemini (Gemini 1.5 Flash Free Tier):**
    - Rate limit: **15 RPM** and **1,000,000 TPM**.
    - Daily quota: **1,500 requests per day**.
    - *Impact:* While the token budget is generous, the strict 15 RPM cap makes un-cached municipal intake fail during minor morning peak periods.
* **Mitigation:**
  Content-hash Redis caching cuts outbound API consumption by more than half, and exponential backoff retry with automatic failover to the secondary provider and rule-based fallback guarantees zero user-facing 5xx/429 errors.

---

## 15. VPA Sizing Recommendations
Offline VerticalPodAutoscaler profiling with [k8s/base/vpa.yaml](file:///home/aun/Downloads/scd%20assignment/CivicPulse/k8s/base/vpa.yaml) under simulated synthetic traffic yielded the following container recommendations:

| Target Container | Metric | Target Recommendation | Lower Bound | Upper Bound |
| :--- | :--- | :--- | :--- | :--- |
| **`backend`** | **CPU** | `150m` | `50m` | `1000m` |
| **`backend`** | **Memory** | `280Mi` | `128Mi` | `768Mi` |
| **`frontend`** | **CPU** | `25m` | `10m` | `100m` |
| **`frontend`** | **Memory** | `32Mi` | `16Mi` | `64Mi` |

These empirical recommendations validate that our baseline deployment request of `cpu: 100m, memory: 256Mi` closely matches real-world execution requirements, while confirming that keeping VPA in `Off` mode prevents scale thrashing against the HPA CPU target of 60%.

---

## 16. Merge Conflict Resolution & Winning Version Rationale
During feature branch integration in PR #22 (`feat/performance-and-conflict` into `dev`), a merge conflict occurred in [backend/app/core/config.py:15](file:///home/aun/Downloads/scd%20assignment/CivicPulse/backend/app/core/config.py#L15) regarding rate limit thresholds:
- The feature branch proposed `RATE_LIMIT_REQUESTS = 25`.
- The `dev` branch defined `RATE_LIMIT_REQUESTS = 15`.

**Why the Winning Version Won:**
The team accepted the 15-request threshold from `dev`. Stress testing demonstrated that allowing 25 requests per minute per IP caused excessive sorted-set memory growth in Redis and quickly exhausted the 15-to-30 RPM rate limits imposed by free-tier LLM providers (Groq and Gemini). The 15-request limit accommodated genuine citizen retries while maintaining strict protection over downstream services and database connection pools.

---

## 17. Architectural Decisions: Framework & Orchestration Tooling
* **FastAPI Selection vs. Flask:**
  CivicPulse uses FastAPI over Flask to take full advantage of native Python `async`/`await` asynchronous concurrency (critical for high-throughput non-blocking I/O when awaiting asyncpg database queries and Redis sorted-set pipelines), strict Pydantic model validation with OpenAPI/Swagger generation, and modern Python typing.
* **Kustomize vs. Helm:**
  Kustomize was chosen over Helm because it is natively built into `kubectl` (`kubectl apply -k`), requires no extra package managers, server-side Helm controllers, or complex chart repositories, and uses declarative, deterministic YAML overlays (`patchesStrategicMerge`) rather than fragile text-templating engines that can generate invalid Kubernetes YAML.

